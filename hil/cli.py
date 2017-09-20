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

"""This module implements the HIL command line tool."""
from hil import config, server, migrations
from hil.config import cfg
from hil.commands.util import ensure_not_root

import inspect
import json
import os
import requests
import sys
import urllib
import schema
import logging

from functools import wraps

from hil.client.client import Client, RequestsHTTPClient, KeystoneHTTPClient
from hil.client.base import FailedAPICallException


logger = logging.getLogger(__name__)
command_dict = {}
usage_dict = {}
MIN_PORT_NUMBER = 1
MAX_PORT_NUMBER = 2**16 - 1


# An instance of HTTPClient, which will be used to make the request.
http_client = None
C = None


class InvalidAPIArgumentsException(Exception):
    """Exception indicating that the user passed invalid arguments."""


def cmd(f):
    """A decorator for CLI commands.

    This decorator firstly adds the function to a dictionary of valid CLI
    commands, secondly adds exception handling for when the user passes the
    wrong number of arguments, and thirdly generates a 'usage' description and
    puts it in the usage dictionary.
    """

    # Build the 'usage' info for the help:
    args, varargs, _, _ = inspect.getargspec(f)
    num_args = len(args)  # used later to validate passed args.
    showee = [f.__name__] + ['<%s>' % name for name in args]
    args = ' '.join(['<%s>' % name for name in args])
    if varargs:
        showee += ['<%s...>' % varargs]
    usage_dict[f.__name__] = ' '.join(showee)

    @wraps(f)
    def wrapped(*args, **kwargs):
        """Wrapper that implements the functionality described above."""
        try:
            # For commands which accept a variable number of arguments,
            # num_args is the *minimum* required arguments; there is no
            # maximum. For other commands, there must be *exactly* `num_args`
            # arguments:
            if len(args) < num_args or not varargs and len(args) > num_args:
                raise InvalidAPIArgumentsException()
            f(*args, **kwargs)
        except InvalidAPIArgumentsException as e:
            if e.message != '':
                sys.stderr.write(e.message + '\n\n')
            sys.stderr.write('Invalid arguments.  Usage:\n')
            help(f.__name__)

    command_dict[f.__name__] = wrapped
    return wrapped


def setup_http_client():
    """Set `http_client` to a valid instance of `HTTPClient`

    and pass it as parameter to initialize the client library.

    Sets http_client to an object which makes HTTP requests with
    authentication. It chooses an authentication backend as follows:

    1. If the environment variables HIL_USERNAME and HIL_PASSWORD
       are defined, it will use HTTP basic auth, with the corresponding
       user name and password.
    2. If the `python-keystoneclient` library is installed, and the
       environment variables:

           * OS_AUTH_URL
           * OS_USERNAME
           * OS_PASSWORD
           * OS_PROJECT_NAME

       are defined, Keystone is used.
    3. Oterwise, do not supply authentication information.

    This may be extended with other backends in the future.

    `http_client` is also passed as a parameter to the client library.
    Until all calls are moved to client library, this will support
    both ways of intereacting with HIL.
    """
    global http_client
    global C  # initiating the client library
    # First try basic auth:
    ep = (
            os.environ.get('HIL_ENDPOINT') or
            sys.stdout.write("Error: HIL_ENDPOINT not set \n")
            )
    basic_username = os.getenv('HIL_USERNAME')
    basic_password = os.getenv('HIL_PASSWORD')
    if basic_username is not None and basic_password is not None:
        # For calls with no client library support yet.
        # Includes all headnode calls; registration of nodes and switches.
        http_client = RequestsHTTPClient()
        http_client.auth = (basic_username, basic_password)
        # For calls using the client library
        C = Client(ep, http_client)
        return
    # Next try keystone:
    try:
        from keystoneauth1.identity import v3
        from keystoneauth1 import session
        os_auth_url = os.getenv('OS_AUTH_URL')
        os_password = os.getenv('OS_PASSWORD')
        os_username = os.getenv('OS_USERNAME')
        os_user_domain_id = os.getenv('OS_USER_DOMAIN_ID') or 'default'
        os_project_name = os.getenv('OS_PROJECT_NAME')
        os_project_domain_id = os.getenv('OS_PROJECT_DOMAIN_ID') or 'default'
        if None in (os_auth_url, os_username, os_password, os_project_name):
            raise KeyError("Required openstack environment variable not set.")
        auth = v3.Password(auth_url=os_auth_url,
                           username=os_username,
                           password=os_password,
                           project_name=os_project_name,
                           user_domain_id=os_user_domain_id,
                           project_domain_id=os_project_domain_id)
        sess = session.Session(auth=auth)
        http_client = KeystoneHTTPClient(sess)
        # For calls using the client library
        C = Client(ep, http_client)
        return
    except (ImportError, KeyError):
        pass
    # Finally, fall back to no authentication:
    http_client = requests.Session()
    C = Client(ep, http_client)


def check_status_code(response):
    """Check the status code of the response.

    If it is a successful status code, print the body of the response to
    stdout. Otherwise, print an error message, and raise a
    FailedAPICallException.
    """
    if response.status_code < 200 or response.status_code >= 300:
        sys.stderr.write('Unexpected status code: %d\n' % response.status_code)
        sys.stderr.write('Response text:\n')
        sys.stderr.write(response.content + "\n")
        raise FailedAPICallException()
    else:
        sys.stdout.write(response.content + "\n")

# Function object_url should be DELETED.


def object_url(*args):
    """Return a url with a prefix of the HIL endpoint, and args as the
    (remaining) segments of the path.

    TODO: This function's name is no longer very accurate.  As soon as it is
    safe, we should change it to something more generic.
    """
    # Prefer an environmental variable for getting the endpoint if available.
    url = os.environ.get('HIL_ENDPOINT')
    if url is None:
        config.setup()
        url = cfg.get('client', 'endpoint')

    for arg in args:
        url += '/' + urllib.quote(arg, '')
    return url


# Helper functions for making HTTP requests against the API.
#    Uses the global variable `http_client` to make the request.
#
#    Arguments:
#
#        `url` - The url to make the request to
#        `data` - the body of the request (for PUT, POST and DELETE)
#        `params` - query parameters (for GET)

def do_put(url, data={}):
    """do a put request and check the response."""
    check_status_code(http_client.request('PUT', url, data=json.dumps(data)))


def do_post(url, data={}):
    """do a post request and check the response."""
    check_status_code(http_client.request('POST', url, data=json.dumps(data)))


def do_get(url, params=None):
    """do a get request and check the response."""
    check_status_code(http_client.request('GET', url, params=params))


def do_delete(url):
    """do a delete request and check the response."""
    check_status_code(http_client.request('DELETE', url))

# DELETE UPTIL HERE once all calls have client library support.


@cmd
def serve(port):
    """Run a development api server. Don't use this in production."""
    try:
        port = schema.And(
            schema.Use(int),
            lambda n: MIN_PORT_NUMBER <= n <= MAX_PORT_NUMBER).validate(port)
    except schema.SchemaError:
        raise InvalidAPIArgumentsException(
            'Error: Invaid port. Must be in the range 1-65535.'
        )
    except Exception as e:
        sys.exit('Unxpected Error!!! \n %s' % e)

    """Start the HIL API server"""
    config.setup()
    if cfg.has_option('devel', 'debug'):
        debug = cfg.getboolean('devel', 'debug')
    else:
        debug = False
    # We need to import api here so that the functions within it get registered
    # (via `rest_call`), though we don't use it directly:
    # pylint: disable=unused-variable
    from hil import api, rest
    server.init()
    migrations.check_db_schema()
    server.stop_orphan_consoles()
    rest.serve(port, debug=debug)


@cmd
def serve_networks():
    """Start the HIL networking server"""
    from hil import model, deferred
    from time import sleep
    config.setup()
    server.init()
    server.register_drivers()
    server.validate_state()
    model.init_db()
    migrations.check_db_schema()

    # Check if config contains usable sleep_time
    if (cfg.has_section('network-daemon') and
            cfg.has_option('network-daemon', 'sleep_time')):
        try:
            sleep_time = cfg.getfloat('network-daemon', 'sleep_time')
        except (ValueError):
            sys.exit("Error: sleep_time set to non-float value")
        if sleep_time <= 0 or sleep_time >= 3600:
            sys.exit("Error: sleep_time not within bounds "
                     "0 < sleep_time < 3600")
        if sleep_time > 60:
            logger.warn('sleep_time greater than 1 minute.')
    else:
        sleep_time = 2

    while True:
        # Empty the journal until it's empty; then delay so we don't tight
        # loop.
        while deferred.apply_networking():
            pass
        sleep(sleep_time)


@cmd
def user_create(username, password, is_admin):
    """Create a user <username> with password <password>.

    <is_admin> may be either "admin" or "regular", and determines whether
    the user has administrative priveledges.
    """
    C.user.create(username, password, is_admin)


@cmd
def user_set_admin(username, is_admin):
    """Changes the admin status of user <username>.

    <is_admin> may by either "admin" or "regular", and determines whether
    a user is authorized for administrative privileges.
    """
    if is_admin not in ('admin', 'regular'):
        raise ValueError(
            "invalid user privilege: must be either 'admin' or 'regular'."
            )
    C.user.set_admin(username, is_admin == 'admin')


@cmd
def network_create(network, owner, access, net_id):
    """Create a link-layer <network>.  See docs/networks.md for details"""
    C.network.create(network, owner, access, net_id)


@cmd
def network_create_simple(network, project):
    """Create <network> owned by project.  Specific case of network_create"""
    C.network.create(network, project, project, "")


@cmd
def network_delete(network):
    """Delete a <network>"""
    C.network.delete(network)


@cmd
def user_delete(username):
    """Delete the user <username>"""
    C.user.delete(username)


@cmd
def list_projects():
    """List all projects"""
    q = C.project.list()
    sys.stdout.write('%s Projects :    ' % len(q) + " ".join(q) + '\n')


@cmd
def user_add_project(user, project):
    """Add <user> to <project>"""
    C.user.add(user, project)


@cmd
def user_remove_project(user, project):
    """Remove <user> from <project>"""
    C.user.remove(user, project)


@cmd
def network_grant_project_access(project, network):
    """Add <project> to <network> access"""
    C.network.grant_access(project, network)


@cmd
def network_revoke_project_access(project, network):
    """Remove <project> from <network> access"""
    C.network.revoke_access(project, network)


@cmd
def project_create(project):
    """Create a <project>"""
    C.project.create(project)


@cmd
def project_delete(project):
    """Delete <project>"""
    C.project.delete(project)


@cmd
def headnode_create(headnode, project, base_img):
    """Create a <headnode> in a <project> with <base_img>"""
    url = object_url('headnode', headnode)
    do_put(url, data={'project': project,
                      'base_img': base_img})


@cmd
def headnode_delete(headnode):
    """Delete <headnode>"""
    url = object_url('headnode', headnode)
    do_delete(url)


@cmd
def project_connect_node(project, node):
    """Connect <node> to <project>"""
    C.project.connect(project, node)


@cmd
def project_detach_node(project, node):
    """Detach <node> from <project>"""
    C.project.detach(project, node)


@cmd
def headnode_start(headnode):
    """Start <headnode>"""
    url = object_url('headnode', headnode, 'start')
    do_post(url)


@cmd
def headnode_stop(headnode):
    """Stop <headnode>"""
    url = object_url('headnode', headnode, 'stop')
    do_post(url)


@cmd
def node_register(node, subtype, *args):
    """Register a node named <node>, with the given type
        if obm is of type: ipmi then provide arguments
        "ipmi", <hostname>, <ipmi-username>, <ipmi-password>
    """
    obm_api = "http://schema.massopencloud.org/haas/v0/obm/"
    obm_types = ["ipmi", "mock"]
    # Currently the classes are hardcoded
    # In principle this should come from api.py
    # In future an api call to list which plugins are active will be added.

    if subtype in obm_types:
        if len(args) == 3:
            obminfo = {"type": obm_api + subtype, "host": args[0],
                       "user": args[1], "password": args[2]
                       }
        else:
            sys.stderr.write('ERROR: subtype ' + subtype +
                             ' requires exactly 3 arguments\n')
            sys.stderr.write('<hostname> <ipmi-username> <ipmi-password>\n')
            return
    else:
        sys.stderr.write('ERROR: Wrong OBM subtype supplied\n')
        sys.stderr.write('Supported OBM sub-types: ipmi, mock\n')
        return

    url = object_url('node', node)
    do_put(url, data={"obm": obminfo})


@cmd
def node_delete(node):
    """Delete <node>"""
    C.node.delete(node)


@cmd
def node_power_cycle(node):
    """Power cycle <node>"""
    C.node.power_cycle(node)


@cmd
def node_power_off(node):
    """Power off <node>"""
    C.node.power_off(node)


@cmd
def node_set_bootdev(node, dev):
    """
    Sets <node> to boot from <dev> persistenly

    eg; hil node_set_bootdev dell-23 pxe
    for IPMI, dev can be set to disk, pxe, or none
    """
    url = object_url('node', node, 'boot_device')
    do_put(url, data={'bootdev': dev})


@cmd
def node_register_nic(node, nic, macaddr):
    """
    Register existence of a <nic> with the given <macaddr> on the given <node>
    """
    C.node.add_nic(node, nic, macaddr)


@cmd
def node_delete_nic(node, nic):
    """Delete a <nic> on a <node>"""
    C.node.remove_nic(node, nic)


@cmd
def headnode_create_hnic(headnode, nic):
    """Create a <nic> on the given <headnode>"""
    url = object_url('headnode', headnode, 'hnic', nic)
    do_put(url)


@cmd
def headnode_delete_hnic(headnode, nic):
    """Delete a <nic> on a <headnode>"""
    url = object_url('headnode', headnode, 'hnic', nic)
    do_delete(url)


@cmd
def node_connect_network(node, nic, network, channel):
    """Connect <node> to <network> on given <nic> and <channel>"""
    C.node.connect_network(node, nic, network, channel)


@cmd
def node_detach_network(node, nic, network):
    """Detach <node> from the given <network> on the given <nic>"""
    C.node.detach_network(node, nic, network)


@cmd
def headnode_connect_network(headnode, nic, network):
    """Connect <headnode> to <network> on given <nic>"""
    url = object_url('headnode', headnode, 'hnic', nic, 'connect_network')
    do_post(url, data={'network': network})


@cmd
def headnode_detach_network(headnode, hnic):
    """Detach <headnode> from the network on given <nic>"""
    url = object_url('headnode', headnode, 'hnic', hnic, 'detach_network')
    do_post(url)


@cmd
def metadata_set(node, label, value):
    """Register metadata with <label> and <value> with <node> """
    url = object_url('node', node, 'metadata', label)
    do_put(url, data={'value': value})


@cmd
def metadata_delete(node, label):
    """Delete metadata with <label> from a <node>"""
    url = object_url('node', node, 'metadata', label)
    do_delete(url)


@cmd
def switch_register(switch, subtype, *args):
    """Register a switch with name <switch> and
    <subtype>, <hostname>, <username>,  <password>
    eg. hil switch_register mock03 mock mockhost01 mockuser01 mockpass01

    FIXME: current design needs to change. CLI should not know about every
    backend. Ideally, this should be taken care of in the driver itself or
    client library (work-in-progress) should manage it.
    """
    switch_api = "http://schema.massopencloud.org/haas/v0/switches/"
    if subtype == "nexus" or subtype == "delln3000":
        if len(args) == 4:
            switchinfo = {
                "type": switch_api + subtype,
                "hostname": args[0],
                "username": args[1],
                "password": args[2],
                "dummy_vlan": args[3]}
        else:
            sys.stderr.write('ERROR: subtype ' + subtype +
                             ' requires exactly 4 arguments\n'
                             '<hostname> <username> <password>'
                             '<dummy_vlan_no>\n')
            return
    elif subtype == "mock":
        if len(args) == 3:
            switchinfo = {"type": switch_api + subtype, "hostname": args[0],
                          "username": args[1], "password": args[2]}
        else:
            sys.stderr.write('ERROR: subtype ' + subtype +
                             ' requires exactly 3 arguments\n')
            sys.stderr.write('<hostname> <username> <password>\n')
            return
    elif subtype == "powerconnect55xx":
        if len(args) == 3:
            switchinfo = {"type": switch_api + subtype, "hostname": args[0],
                          "username": args[1], "password": args[2]}
        else:
            sys.stderr.write('ERROR: subtype ' + subtype +
                             ' requires exactly 3 arguments\n'
                             '<hostname> <username> <password>\n')
            return
    elif subtype == "brocade" or "dellnos9":
        if len(args) == 4:
            switchinfo = {"type": switch_api + subtype, "hostname": args[0],
                          "username": args[1], "password": args[2],
                          "interface_type": args[3]}
        else:
            sys.stderr.write('ERROR: subtype ' + subtype +
                             ' requires exactly 4 arguments\n'
                             '<hostname> <username> <password> '
                             '<interface_type>\n'
                             'NOTE: interface_type refers '
                             'to the speed of the switchports\n '
                             'ex. TenGigabitEthernet, FortyGigabitEthernet, '
                             'etc.\n')
            return
    else:
        sys.stderr.write('ERROR: Invalid subtype supplied\n')
        return
    url = object_url('switch', switch)
    do_put(url, data=switchinfo)


@cmd
def switch_delete(switch):
    """Delete a <switch> """
    C.switch.delete(switch)


@cmd
def list_switches():
    """List all switches"""
    q = C.switch.list()
    sys.stdout.write('%s switches :    ' % len(q) + " ".join(q) + '\n')


@cmd
def port_register(switch, port):
    """Register a <port> with <switch> """
    C.port.register(switch, port)


@cmd
def port_delete(switch, port):
    """Delete a <port> from a <switch>"""
    C.port.delete(switch, port)


@cmd
def port_connect_nic(switch, port, node, nic):
    """Connect a <port> on a <switch> to a <nic> on a <node>"""
    C.port.connect_nic(switch, port, node, nic)


@cmd
def port_detach_nic(switch, port):
    """Detach a <port> on a <switch> from whatever's connected to it"""
    C.port.detach_nic(switch, port)


@cmd
def port_revert(switch, port):
    """Detach a <port> on a <switch> from all attached networks."""
    C.port.port_revert(switch, port)


@cmd
def list_network_attachments(network, project):
    """List nodes connected to a network
    <project> may be either "all" or a specific project name.
    """
    url = object_url('network', network, 'attachments')

    if project == "all":
        do_get(url)
    else:
        do_get(url, params={'project': project})


@cmd
def list_nodes(is_free):
    """List all nodes or all free nodes

    <is_free> may be either "all" or "free", and determines whether
        to list all nodes or all free nodes.
    """
    q = C.node.list(is_free)
    if is_free == 'all':
        sys.stdout.write('All nodes %s\t:    %s\n' % (len(q), " ".join(q)))
    elif is_free == 'free':
        sys.stdout.write('Free nodes %s\t:   %s\n' % (len(q), " ".join(q)))
    else:
        sys.stdout.write('Error: %s is an invalid argument\n' % (is_free))


@cmd
def list_project_nodes(project):
    """List all nodes attached to a <project>"""
    q = C.project.nodes_in(project)
    sys.stdout.write('Nodes allocated to %s:  ' % project + " ".join(q) + '\n')


@cmd
def list_project_networks(project):
    """List all networks attached to a <project>"""
    q = C.project.networks_in(project)
    sys.stdout.write(
            "Networks allocated to %s\t:   %s\n" % (project, " ".join(q))
            )


@cmd
def show_switch(switch):
    """Display information about <switch>"""
    q = C.switch.show(switch)
    for item in q.items():
        sys.stdout.write("%s\t  :  %s\n" % (item[0], item[1]))


@cmd
def show_port(switch, port):
    """Show what's connected to <port>"""
    print C.port.show(switch, port)


@cmd
def list_networks():
    """List all networks"""
    q = C.network.list()
    for item in q.items():
        sys.stdout.write('%s \t : %s\n' % (item[0], item[1]))


@cmd
def show_network(network):
    """Display information about <network>"""
    q = C.network.show(network)
    for item in q.items():
        sys.stdout.write("%s\t  :  %s\n" % (item[0], item[1]))


@cmd
def show_node(node):
    """Display information about a <node>

    FIXME: Recursion should be implemented to the output.
    """
#    The output of show_node is a dictionary that can be list of list, having
#    multiple nics and networks. More metadata about node could be shown
#    via this call. Suggestion to future developers of CLI to use
#    recursion in the call for output of such metadata.

    q = C.node.show(node)
    for item in q.items():
        sys.stdout.write("%s\t  :  %s\n" % (item[0], item[1]))


@cmd
def list_project_headnodes(project):
    """List all headnodes attached to a <project>"""
    url = object_url('project', project, 'headnodes')
    do_get(url)


@cmd
def show_headnode(headnode):
    """Display information about a <headnode>"""
    url = object_url('headnode', headnode)
    do_get(url)


@cmd
def list_headnode_images():
    """Display registered headnode images"""
    url = object_url('headnode_images')
    do_get(url)


@cmd
def show_console(node):
    """Display console log for <node>"""
    url = object_url('node', node, 'console')
    do_get(url)


@cmd
def start_console(node):
    """Start logging console output from <node>"""
    C.node.start_console(node)


@cmd
def stop_console(node):
    """Stop logging console output from <node> and delete the log"""
    C.node.stop_console(node)


@cmd
def create_admin_user(username, password):
    """Create an admin user. Only valid for the database auth backend.

    This must be run on the HIL API server, with access to hil.cfg and the
    database. It will create an user named <username> with password
    <password>, who will have administrator privileges.

    This command should only be used for bootstrapping the system; once you
    have an initial admin, you can (and should) create additional users via
    the API.
    """
    config.setup()
    if not config.cfg.has_option('extensions', 'hil.ext.auth.database'):
        sys.exit("'make_inital_admin' is only valid with the database auth"
                 " backend.")
    from hil import model
    from hil.model import db
    from hil.ext.auth.database import User
    model.init_db()
    db.session.add(User(label=username, password=password, is_admin=True))
    db.session.commit()


@cmd
def list_active_extensions():
    """List active extensions by type. """
    all_extensions = C.extensions.list_active()
    if not all_extensions:
        print "No active extensions"
    else:
        for ext in all_extensions:
            print ext


@cmd
def help(*commands):
    """Display usage of all following <commands>, or of all commands if none
    are given
    """
    if not commands:
        sys.stdout.write('Usage: %s <command> <arguments...> \n' % sys.argv[0])
        sys.stdout.write('Where <command> is one of:\n')
        commands = sorted(command_dict.keys())
    for name in commands:
        # For each command, print out a summary including the name, arguments,
        # and the docstring (as a #comment).
        sys.stdout.write('  %s\n' % usage_dict[name])
        sys.stdout.write('      %s\n' % command_dict[name].__doc__)


def main():
    """Entry point to the CLI.

    There is a script located at ${source_tree}/scripts/hil, which invokes
    this function.
    """
    ensure_not_root()

    if len(sys.argv) < 2 or sys.argv[1] not in command_dict:
        # Display usage for all commands
        help()
        sys.exit(1)
    else:
        setup_http_client()
        try:
            command_dict[sys.argv[1]](*sys.argv[2:])
        except FailedAPICallException as e:
            sys.exit('Error: %s\n' % e.message)
        except InvalidAPIArgumentsException as e:
            sys.exit('Error: %s\n' % e.message)
        except Exception as e:
            sys.exit('Unexpected error: %s\n' % e.message)
