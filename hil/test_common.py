"""Misc. utilities for use in the test suite.

Modules outside of the test suite are not permitted to import this module.
TODO: we should separate this out from the main package.
"""

from hil.migrations import create_db
from hil.network_allocator import get_network_allocator
from hil.config import cfg
from hil.rest import app, init_auth
from hil.model import db, init_db, Node, Nic, Network, Project, Headnode, \
    Hnic, Switch, Port, Metadata
from hil import api, config, server
from abc import ABCMeta, abstractmethod
import json
import subprocess
import sys
import os
import os.path
import logging
import tempfile
import time
import socket
import re
from urlparse import urlparse
from base64 import urlsafe_b64encode
from hil.client.client import HTTPClient, RequestsHTTPClient, HTTPResponse

uuid_pattern = re.compile(
            "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


class HybridHTTPClient(HTTPClient):
    """Implementation of HTTPClient for use in testing.

    Depending on the URL, this uses either Flask's test client,
    or a RequestsHTTPClient. This allows us to do testing without
    launching a separate process for the API server, while still
    being able to talk to external services (like OBMd and keystone).

    Parameters
    ----------

    endpoint : str
        The endpoint for the HIL server
    username : str or None
        The username to authenticate as
    password : str or None
        The password to authenticate with

    If username and password are not specified, not authentication is used,
    otherwise they are used for HTTP basic auth. It is an error to specify
    one and not the other.
    """

    def __init__(self, endpoint, username=None, password=None):
        if (username is None) != (password is None):
            assert False, (
                "You must either specify both username and password, "
                "or neither."
            )
        self._flask_client = app.test_client()
        self._requests_client = RequestsHTTPClient()
        self._endpoint = endpoint
        self._username = username
        self._password = password

    def request(self, method, url, data=None, params=None):
        # Manually follow redirects. We can't just rely on flask to do it,
        # since if we get redirected to something outside of the app, we
        # want to switch to a different client.
        resp = self._make_request(method, url, data=data, params=params)
        while self._is_redirect(resp):
            url = resp.headers['Location']
            resp = self._make_request(method, url, data=data, params=params)
        return resp

    @staticmethod
    def _is_redirect(resp):
        """Return whether `resp` is a redirect response."""
        return resp.status_code == 307

    def _make_request(self, method, url, data, params):
        """Make an HTTP Request.

        This is a helper method for `request`. It handles making a request,
        but does not itself follow redirects.
        """
        if urlparse(url).netloc == urlparse(self._endpoint).netloc:
            # Url is within the Flask app; use Flask's test client.

            if self._username is None:
                # Username and password not specified; don't set an
                # Authorization header.
                headers = {}
            else:
                headers = {
                    # Flask doesn't provide a straightforward way to do basic
                    # auth, but it's not actually that complicated:
                    'Authorization': 'Basic ' + urlsafe_b64encode(
                        self._username + ':' + self._password
                    ),
                }

            resp = self._flask_client.open(
                method=method,
                headers=headers,
                # flask expects just a path, and assumes
                # the host & scheme:
                path=urlparse(url).path,
                data=data,
                query_string=params,
            )
            return HTTPResponse(status_code=resp.status_code,
                                headers=resp.headers,
                                # As far as I(zenhack) can tell, flask's test
                                # client doesn't support streaming, so we just
                                # return a one-shot iterator. This is
                                # conceptually not ideal, but fine in practice
                                # because the HIL api server doesn't do any
                                # streaming anyway; we only need that
                                # functionality with requests that go to OBMd.
                                body=iter([resp.get_data()]))
        else:
            # URL is outside of our flask app; use the real http client.
            return self._requests_client.request(method,
                                                 url,
                                                 data=data,
                                                 params=params)


def server_init():
    """Fixture to do server-specific setup."""
    server.register_drivers()
    server.validate_state()


def config_testsuite():
    """Loads an initial config from ``testsuite.cfg``.

    This is meant to be used as/from a pytest fixture, but isn't declared
    here as such; individual modules should declare fixtures which use it.

    Tests which don't care about a specific configuration should leave the
    config alone. This allows the developer to test with different
    configurations, e.g. different DBMS backends.

    if testsuite.cfg doesn't exist, sane defaults are provided.
    """
    # NOTE: The file ``testsuite.cfg.default`` Should be updated whenever
    # The default settings here are modified.
    if os.path.isfile('testsuite.cfg'):
        config.load('testsuite.cfg')
    else:
        config_set({
            'extensions': {
                # Use the null network allocator and auth plugin by default:
                'hil.ext.network_allocators.null': '',
                'hil.ext.auth.null': '',
            },
            'devel': {
                'dry_run': 'True',
            },
            'headnode': {
                'base_imgs': 'base-headnode, img1, img2, img3, img4',
            },
            'database': {
                'uri': 'sqlite:///:memory:',
            }
        })


def config_merge(config_dict):
    """Modify the configuration according to ``config_dict``.

    ``config_dict`` should be a dictionary mapping section names (strings)
    to dictionaries mapping option names within a section (again, strings)
    to their values. If the value of a section, or option is None, that
    section or option is removed. Otherwise, the section is created if it
    does not exist, and any options are set to the specified values.
    """
    for section in config_dict.keys():
        if config_dict[section] is None:
            print('remove section: %r' % section)
            cfg.remove_section(section)
        else:
            if not cfg.has_section(section):
                print('add section: %r' % section)
                cfg.add_section(section)
            for option in config_dict[section].keys():
                if config_dict[section][option] is None:
                    print('remove option: %r' % option)
                    cfg.remove_option(section, option)
                else:
                    assert isinstance(config_dict[section][option], str), (
                        "Passed a non-string value in config!"
                    )
                    print('set option: %r' % option)
                    cfg.set(section, option, config_dict[section][option])


def config_set(config_dict):
    """Set the configuration according to ``config_dict``.

    This works like ``config_merge``, except that it starts from an empty
    configuration.
    """
    config_clear()
    config_merge(config_dict)


def config_clear():
    """Clear the contents of the current HIL configuration"""
    for section in cfg.sections():
        cfg.remove_section(section)


def network_create_simple(network, project):
    """Create a simple project-owned network.

    This is a shorthand for the network_create API call, that defaults
    parameters to the most common case---namely, that the network is owned by
    a project, has access only by that project, and uses an allocated
    underlying net_id.  Note that this is the only valid set of parameters for
    a network that belongs to a project.

    The test-suite uses this extensively, for tests that don't care about more
    complicated features of networks.
    """
    api.network_create(network, project, project, "")


def newDB():
    """Configures and returns a connection to a freshly initialized DB."""
    with app.app_context():
        init_db()
        create_db()


def releaseDB():
    """Do we need to do anything here to release resources?"""
    with app.app_context():
        db.drop_all()


def fresh_database(request):
    """Runs the test against a newly populated DB.

    This is meant to be used as a pytest fixture, but isn't declared
    here as such; individual modules should declare it as a fixture.

    This must run *after* the config file (or equivalent) has been loaded.
    """
    newDB()
    request.addfinalizer(lambda: releaseDB())


def with_request_context():
    """Run the test inside of a request context.

    This combines flask's request context with our own setup. It is intended
    to be used via pytests' `yield_fixture`, but like the other fixtures in
    this module, must be declared as such in the test module itself.
    """
    with app.test_request_context():
        init_auth()
        yield


def fail_on_log_warnings():
    """Raise an exception if a message is logged at warning level or higher.

    Calling this registers a Handler for the `hil` module; it is meant to be
    used as a test fixture.

    The exception raised will be of type `LoggedWarningError`.
    """
    logger = logging.getLogger('hil')
    logger.addHandler(_FailOnLogWarnings())


class _FailOnLogWarnings(logging.Handler):
    """The Handler type used by the `fail_on_log_warnings` fixture."""

    def emit(self, record):
        if record.levelno >= logging.WARNING:
            raise LoggedWarningError(record)


class LoggedWarningError(Exception):
    """Error indicating that a message was logged at warning level or higher.

    Used by `fail_on_log_warnings`
    """

    def __init__(self, record):
        self.record = record

    def __repr__(self):
        return 'LoggedWarningError(%r)' % self.record


class ModelTest:
    """Superclass with tests common to all models.

    Inheriting from ``ModelTest`` will generate tests in the subclass (each
    of the methods beginning with ``test_`` below), but the ``ModelTest`` class
    itself does not generate tests. (pytest will ignore it because the name of
    the class does not start with ``Test`).
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def sample_obj(self):
        """returns a sample object, which can be used for various tests.

        There aren't really any specific requirements for the object, just that
        it be "valid."
        """

    def test_repr(self):
        """Test that printing the sample object doesn't explode.

        Early on there were a few bugs where __repr__ threw an exception.
        """
        print(self.sample_obj())

    def test_insert(self):
        """Test inserting the sample object into the database.
        """
        db.session.add(self.sample_obj())


class NetworkTest:
    """Superclass for network-related deployment tests"""

    def get_port_networks(self, ports):
        """Get the networks associated with ports.

        ports is a list of Port objects.

        The return value is like that of
        Switch.session().get_port_networks(), except that it includes the
        results for all of the port objects listed.
        """
        ret = {}
        ports_by_switch = {}
        for port in ports:
            if port.owner not in ports_by_switch:
                ports_by_switch[port.owner] = []
            ports_by_switch[port.owner].append(port)
        for switch, ports in ports_by_switch.iteritems():
            session = switch.session()
            switch_port_networks = session.get_port_networks(ports)
            session.disconnect()
            for k, v in switch_port_networks.iteritems():
                ret[k] = v
        return ret

    def get_network(self, port, port_networks):
        """Returns all interfaces on the same network as a given port"""
        if port not in port_networks:
            return set()
        result = set()
        for k, v in port_networks.iteritems():
            networks = set([net for _channel, net in v])
            for _, net in port_networks[port]:
                if net in networks:
                    result.add(k)
        return result

    def get_all_ports(self, nodes):
        """Return all ports that the node is attached to.

        nodes is a list of Node objects.

        The return value is a list of Port objects.
        """
        ports = []
        for node in nodes:
            for nic in node.nics:
                ports.append(nic.port)
        return ports

    def collect_nodes(self):
        """Add 4 available nodes with nics to the project.

        If there are not enough nodes, this will rais an api.AllocationError.
        """
        free_nodes = Node.query.filter_by(project_id=None).all()
        nodes = []
        for node in free_nodes:
            if len(node.nics) > 0:
                api.project_connect_node('anvil-nextgen', node.label)
                nodes.append(node)
                if len(nodes) >= 4:
                    break

        # If there are not enough nodes with nics, raise an exception
        if len(nodes) < 4:
            raise api.AllocationError(
                ('At least 4 nodes with at least ' +
                 '1 NIC are required for this test. Only %d node(s) were ' +
                 'provided.') %
                len(nodes))
        return nodes


def site_layout():
    """Load the file site-layout.json, and populate the database accordingly.

    This is meant to be used as a pytest fixture, but isn't declared
    here as such; individual modules should declare it as a fixture.

    Full documentation for the site-layout.json file format is located in
    ``docs/testing.md``.
    """
    layout_json_data = open('site-layout.json')
    layout = json.load(layout_json_data)
    layout_json_data.close()

    for switch in layout['switches']:
        api.switch_register(**switch)

    for node in layout['nodes']:
        api.node_register(
            node=node['name'],
            obm=node['obm'],
            obmd=node['obmd'],
        )
        for nic in node['nics']:
            api.node_register_nic(node['name'], nic['name'], nic['mac'])
            api.switch_register_port(nic['switch'], nic['port'])
            api.port_connect_nic(nic['switch'], nic['port'],
                                 node['name'], nic['name'])


def obmd_cfg():
        """Fixture launching obmd with a config.

        The fixture yields the config as a parsed json object. The obmd
        process is terminated when the test completes.

        Like many of the functions in this module, this is intended to
        be used as a fixture, but not declared here as such; individual
        modules should declare it as a fixture.
        """
        # Make the port number a function of which worker we're running on,
        # so parallel tests don't try to use the same port. We derive the
        # port number by stripping out all non-digit characters from the
        # worker id, and then adding the result to a base. If the worker id
        # isn't set, we're probably not running in parallel, so just use
        # the base.
        portno = 8800
        worker = os.getenv('PYTEST_XDIST_WORKER')
        if worker is not None:
            portno += int(''.join([
                char
                for char in worker
                if char.isdigit()
            ]))

        cfg = {
            'ListenAddr': ":" + str(portno),
            'AdminToken': "8fcfe5d3f8ca8c4b87d0f8ae86b43bca",
            'DBType': 'sqlite3',
            'DBPath': ':memory:',
        }

        (fd, name) = tempfile.mkstemp()
        os.write(fd, json.dumps(cfg))
        os.close(fd)
        try:
            obmd_proc = subprocess.Popen(['obmd', '-config', name])
        except Exception as e:
            assert False, ("Error spawning obmd: %r" % e)

        # wait for obmd to start accepting connections:
        attempts = 0
        while attempts < 60:
            try:
                conn = socket.create_connection(('127.0.0.1', portno))
                conn.close()
                break
            except socket.error:
                time.sleep(0.1)
                attempts += 1
        assert attempts < 60, "Timeout waiting for obmd to start"

        yield cfg

        obmd_proc.terminate()
        obmd_proc.wait()
        os.remove(name)


def headnode_cleanup(request):
    """Clean up headnode VMs left by tests.

    This is meant to be used as a pytest fixture, but isn't declared
    here as such; individual modules should declare it as a fixture.

    This is to work around an irritating bug in some versions of libvirt, which
    causes 'virsh undefine' to fail if called too quickly.  This decorator
    depends on the database containing an accurate list of headnodes.
    """

    def undefine_headnodes():
        """Delete all of the headnodes."""
        for hn in Headnode.query:
            # XXX: Our current version of libvirt has a bug that causes this
            # command to hang for a minute and throw an error before
            # completing successfully.  For this reason, we are ignoring any
            # errors thrown by 'virsh undefine'. This should be changed once
            # we start using a version of libvirt that has fixed this bug.
            #
            # TODO: the above was written *years* ago; we should check if this
            # is still true for any system that we care about, and if not,
            # stop silencing the error.
            try:
                hn.delete()
            except subprocess.CalledProcessError:
                pass

    request.addfinalizer(undefine_headnodes)


def additional_db():
    """ Populated database with additional objects needed for testing.

    The database setup in initial_db is required to remain static as
    a starting point for database migrations so any changes needed for
    testing should be made in additional_db.
    """

    initial_db()

    switch = db.session.query(Switch).filter_by(label="stock_switch_0").one()
    manhattan = db.session.query(Project).filter_by(label="manhattan").one()
    runway = db.session.query(Project).filter_by(label="runway").one()

    with app.app_context():
        for node_label in ['runway_node_0', 'runway_node_1',
                           'manhattan_node_0', 'manhattan_node_1']:

            node = db.session.query(Node).filter_by(label=node_label).one()
            nic = db.session.query(Nic).filter_by(owner=node,
                                                  label='boot-nic').one()

            port = Port('connected_port_0', switch)
            port.nic = nic
            nic.port = port

        networks = [
            {
                'owner': None,
                'access': [manhattan, runway],
                'allocated': False,
                'network_id': 'manhattan_runway_provider_chan',
                'label': 'manhattan_runway_provider',
            },
            {
                'owner': manhattan,
                'access': [manhattan, runway],
                'allocated': True,
                'label': 'manhattan_runway_pxe',
            },
        ]

        for net in networks:
            if net['allocated']:
                net['network_id'] = \
                    get_network_allocator().get_new_network_id()
            db.session.add(Network(**net))
            db.session.add(node)

        db.session.add(switch)
        node = db.session.query(Node).filter_by(label='runway_node_0').one()
        db.session.add(Metadata('EK', 'pk', node))
        db.session.add(Metadata('SHA256', 'b5962d8173c14e60259211bcf25d1263c36'
                                'e0ad7da32ba9d07b224eac1834813', node))
        db.session.commit()


def initial_db():
    """Populates the database with a useful set of objects.

    This allows us to avoid some boilerplate in tests which need a few objects
    in the database in order to work.

    Is static to allow database migrations to be tested, if new objects need
    to be added they should be included in additional_db not initial_db.

    Note that this fixture requires the use of the following extension:

        - hil.ext.switches.mock
    """
    for required_extension in ['hil.ext.switches.mock']:
        assert required_extension in sys.modules, \
            "The 'initial_db' fixture requires the extension %r" % \
            required_extension

    from hil.ext.switches.mock import MockSwitch

    with app.app_context():
        # Create a couple projects:
        runway = Project("runway")
        manhattan = Project("manhattan")
        for proj in [runway, manhattan]:
            db.session.add(proj)

        # ...including at least one with nothing in it:
        db.session.add(Project('empty-project'))

        # ...A variety of networks:

        networks = [
            {
                'owner': None,
                'access': [],
                'allocated': True,
                'label': 'stock_int_pub',
            },
            {
                'owner': None,
                'access': [],
                'allocated': False,
                'network_id': 'ext_pub_chan',
                'label': 'stock_ext_pub',
            },
            {
                # For some tests, we want things to initially be attached to a
                # network. This one serves that purpose; using the others would
                # interfere with some of the network_delete tests.
                'owner': None,
                'access': [],
                'allocated': True,
                'label': 'pub_default',
            },
            {
                'owner': runway,
                'access': [runway],
                'allocated': True,
                'label': 'runway_pxe'
            },
            {
                'owner': None,
                'access': [runway],
                'allocated': False,
                'network_id': 'runway_provider_chan',
                'label': 'runway_provider',
            },
            {
                'owner': manhattan,
                'access': [manhattan],
                'allocated': True,
                'label': 'manhattan_pxe'
            },
            {
                'owner': None,
                'access': [manhattan],
                'allocated': False,
                'network_id': 'manhattan_provider_chan',
                'label': 'manhattan_provider',
            },
        ]

        for net in networks:
            if net['allocated']:
                net['network_id'] = \
                    get_network_allocator().get_new_network_id()
            db.session.add(Network(**net))

        # ... Two switches. One of these is just empty, for testing deletion:
        db.session.add(MockSwitch(label='empty-switch',
                                  hostname='empty',
                                  username='alice',
                                  password='secret',
                                  type=MockSwitch.api_name))

        # ... The other we'll actually attach stuff to for other tests:
        switch = MockSwitch(label="stock_switch_0",
                            hostname='stock',
                            username='bob',
                            password='password',
                            type=MockSwitch.api_name)

        # ... Some free ports:
        db.session.add(Port('free_port_0', switch))
        db.session.add(Port('free_port_1', switch))

        # ... Some nodes (with projets):
        nodes = [
            {'label': 'runway_node_0', 'project': runway},
            {'label': 'runway_node_1', 'project': runway},
            {'label': 'manhattan_node_0', 'project': manhattan},
            {'label': 'manhattan_node_1', 'project': manhattan},
            {'label': 'free_node_0', 'project': None},
            {'label': 'free_node_1', 'project': None},
        ]
        for node_dict in nodes:
            node = Node(
                label=node_dict['label'],
                obmd_uri='http://obmd.example.com/nodes/'+node_dict['label'],
                obmd_admin_token='secret',
            )
            node.project = node_dict['project']
            db.session.add(Nic(node, label='boot-nic', mac_addr='Unknown'))

            # give it a nic that's attached to a port:
            port_nic = Nic(node, label='nic-with-port', mac_addr='Unknown')
            port = Port(node_dict['label'] + '_port', switch)
            port.nic = port_nic

        # ... Some headnodes:
        headnodes = [
            {'label': 'runway_headnode_on',
             'project': runway,
             'on': True},
            {'label': 'runway_headnode_off',
             'project': runway,
             'on': False},
            {'label': 'runway_manhattan_on',
             'project': manhattan,
             'on': True},
            {'label': 'runway_manhattan_off',
             'project': manhattan,
             'on': False},
        ]
        for hn_dict in headnodes:
            headnode = Headnode(hn_dict['project'],
                                hn_dict['label'],
                                'base-headnode')
            headnode.dirty = not hn_dict['on']
            hnic = Hnic(headnode, 'pxe')
            db.session.add(hnic)

            # Connect them to a network, so we can test detaching.
            hnic = Hnic(headnode, 'public')
            hnic.network = Network.query \
                .filter_by(label='pub_default').one()

        # ... and at least one node with no nics (useful for testing delete):
        db.session.add(
            Node(
                label='no_nic_node',
                obmd_uri='http://obmd.example.com/nodes/no_nic_node',
                obmd_admin_token='secret',
            )
        )

        db.session.commit()


def spoof_enable_obm(nodename):
    """spoof "enabling" the named node's obm.

    Stores a phony token in the node's obmd_node_token. This is necessary
    for tests where we can't actually get a token from obmd, but need to run
    other tests that will check for a token.
    """
    node = api.get_or_404(Node, nodename)
    node.obmd_node_token = '0123456789'
    db.session.commit()
