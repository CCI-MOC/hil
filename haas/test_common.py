# Copyright 2013-2014 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

from haas.model import *
from haas.config import cfg
from haas import api, config, rest
from StringIO import StringIO
import json
import subprocess
import sys
import os.path

from werkzeug.wrappers import Request


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
                # Use the null network allocator for these tests
                'haas.ext.network_allocators.null': '',
            },
            'devel': {
                'dry_run': True,
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
    """Clear the contents of the current HaaS configuration"""
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
    init_db(create=True)
    return Session()

def releaseDB(db):
    """Do we need to do anything here to release resources?"""
    db.close_all()
    # According to the documentation, we shouldn't need the Session().bind, but this
    # breaks without it.
    Base.metadata.drop_all(Session().bind)

def fresh_database(request):
    """Runs the test against a newly populated DB.

    This is meant to be used as a pytest fixture, but isn't declared
    here as such; individual modules should declare it as a fixture.

    This must run *after* the config file (or equivalent) has been loaded.
    """
    db = newDB()
    request.addfinalizer(lambda: releaseDB(db))
    return db


class NetworkTest:
    """Superclass for network-related deployment tests"""

    def get_port_networks(self, ports):
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
            networks = set([net for channel, net in v])
            for _, net in port_networks[port]:
                if net in networks:
                    result.add(k)
        return result

    def get_all_ports(self, nodes):
        ports = []
        for node in nodes:
            for nic in node.nics:
                ports.append(nic.port)
        return ports

    def collect_nodes(self, db):
        """Add 4 available nodes with nics to the project.

        If there are not enough nodes, this will rais an api.AllocationError.
        """
        free_nodes = db.query(Node).filter_by(project_id=None).all()
        nodes = []
        for node in free_nodes:
            if len(node.nics) > 0:
                api.project_connect_node('anvil-nextgen', node.label)
                nodes.append(node)
                if len(nodes) >= 4:
                    break

        # If there are not enough nodes with nics, raise an exception
        if len(nodes) < 4:
            raise api.AllocationError(('At least 4 nodes with at least ' +
                '1 NIC are required for this test. Only %d node(s) were ' +
                'provided.') % len(nodes))
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
        api.node_register(node['name'], node['ipmi']['host'],
            node['ipmi']['user'], node['ipmi']['pass'])
        for nic in node['nics']:
            api.node_register_nic(node['name'], nic['name'], nic['mac'])
            api.switch_register_port(nic['switch'], nic['port'])
            api.port_connect_nic(nic['switch'], nic['port'], node['name'], nic['name'])


def headnode_cleanup(request):
    """Clean up headnode VMs left by tests.

    This is meant to be used as a pytest fixture, but isn't declared
    here as such; individual modules should declare it as a fixture.

    This is to work around an irritating bug in some versions of libvirt, which
    causes 'virsh undefine' to fail if called too quickly.  This decorator
    depends on the database containing an accurate list of headnodes.
    """

    def undefine_headnodes():
        db = Session()
        for hn in db.query(Headnode):
            # XXX: Our current version of libvirt has a bug that causes this
            # command to hang for a minute and throw an error before
            # completing successfully.  For this reason, we are ignoring any
            # errors thrown by 'virsh undefine'. This should be changed once
            # we start using a version of libvirt that has fixed this bug.
            try:
                hn.delete()
            except subprocess.CalledProcessError:
                pass

    request.addfinalizer(undefine_headnodes)


def wsgi_mkenv(method, path, data=None):
    """Helper routine to build a wsgi environment.

    We need this to generate mock requests.
    """
    env = {
        'REQUEST_METHOD': method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'SERVER_NAME': 'haas.test-env',
        'SERVER_PORT': '5000',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.errors': sys.stderr,
        'wsgi.multithreaded': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }
    if data is None:
        env['wsgi.input'] = StringIO()
    else:
        env['wsgi.input'] = StringIO(data)
    return env


def do_request(method, path, data=None):
    """Submit a fake HTTP api call.

    This invokes the request handler with an HTTP request corresponding to
    the given arguments.
    """
    response = rest.request_handler(Request(wsgi_mkenv(method, path, data)))
    rest.local_manager.cleanup()
    return response
