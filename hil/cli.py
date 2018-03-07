#!/usr/bin/env python

import sys
import os
import schema

import pkg_resources
import click
import requests

from hil.client.client import Client, RequestsHTTPClient
from hil.client.base import FailedAPICallException
from hil.errors import BadArgumentError
from hil.commands.util import ensure_not_root


VERSION = pkg_resources.require('hil')[0].version

# An instance of HTTPClient, which will be used to make the request.
http_client = None
C = None

class InvalidAPIArgumentsException(Exception):
    """Exception indicating that the user passed invalid arguments."""

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


###############################
### First level subcommands ###
###############################

@click.group()
def cli():
    """The HIL Command line"""

@cli.group()
def node():
    """Commands related to node"""

@cli.group()
def project():
    """Commands related to project"""

@cli.group()
def network():
    """Commands related to network"""

@cli.group()
def switch():
    """Commands related to switch"""

@cli.group()
def port():
    """Commands related to port"""

@cli.group()
def user():
    """Commands related to user"""

######################################
## HIL ADMIN Commands (to be moved) ##
######################################

@cli.command(name='serve', help='Run a development HIL server')
@click.argument('port', type=click.IntRange(0,2**16-1),
                default='5000', required=False)
def serve(port):
    """Run a development api server. Don't use this in production."""
    port = int(port)
    from hil import rest, server, config, migrations
    from hil.config import cfg
    config.setup()
    if cfg.has_option('devel', 'debug'):
        debug = cfg.getboolean('devel', 'debug')
    else:
        debug = False
    # We need to import api here so that the functions within it get registered
    # (via `rest_call`), though we don't use it directly:
    # pylint: disable=unused-variable
    from hil import api
    server.init()
    migrations.check_db_schema()
    server.stop_orphan_consoles()
    rest.serve(port, debug=debug)


@cli.command(name='serve_networks', help='Run the networking server')
def serve_networks():
    """Start the HIL networking server"""
    from hil import model, deferred, config
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

#################################
### NODE SUBCOMMANDS GO HERE! ###
#################################

@node.command(name='list', help='List all or free nodes')
@click.argument('free', type=click.Choice(['free', 'all']),
                default='all', required=False)
def nodes_list(free):
    """List all nodes or all free nodes"""
    q = C.node.list(free)
    if free == 'all':
        sys.stdout.write('All nodes %s\t:    %s\n' % (len(q), " ".join(q)))
    else:
        sys.stdout.write('Free nodes %s\t:   %s\n' % (len(q), " ".join(q)))


@node.command(name='show', help='Show node information')
@click.argument('node')
def node_show(node):
    q = C.node.show(node)
    for item in q.items():
        sys.stdout.write("%s\t  :  %s\n" % (item[0], item[1]))


@node.command(name='bootdev', help="Set a node's boot device")
@click.argument('node')
@click.argument('bootdev')
def node_bootdev(node, bootdev):
    """
    Sets <node> to boot from <dev> persistently

    eg; hil node_set_bootdev dell-23 pxe
    for IPMI, dev can be set to disk, pxe, or none
    """
    C.node.set_bootdev(node, dev)


@node.command(name='register', help='Register a node')
@click.argument('node')
@click.argument('obmtype')
@click.argument('hostname')
@click.argument('username')
@click.argument('password')
def node_register(node, obmtype, hostname, username, password):
    """Register a node named <node>, with the given type
        if obm is of type: ipmi then provide arguments
        "ipmi", <hostname>, <ipmi-username>, <ipmi-password>
    """
    C.node.register(node, obmtype, hostname, username, password)

@node.command(name='delete', help='Delete a node')
@click.argument('node')
def node_delete(node):
    """Delete <node>"""
    C.node.delete(node)


###########################
# node connect/detach network implementations. Could also be expanded to do
# node connect/detach project if need be.

@node.group(name='connect', help='Connect node to an <object>')
def node_connect():
    """Connect node an <object>"""

@node_connect.command(name='network', help="Connect a node to a network")
@click.argument('node')
@click.argument('network')
@click.argument('nic')
@click.argument('channel', default='', required=False)
def node_connect_network(node, network, nic, channel):
    """Connect <node> to <network> on given <nic> and <channel>"""
    print C.node.connect_network(node, nic, network, channel)


@node.group(name='detach', help='Detach node from an <object>')
def node_detach():
    """Connect node an <object>"""


@node_detach.command(name='network', help="Detach node from a network")
@click.argument('node')
@click.argument('network')
@click.argument('nic')
def node_detach_network(node, network, nic):
    """Detach <node> from the given <network> on the given <nic>"""
    print C.node.detach_network(node, nic, network)

###########################
# I could also implement this the way I am doing list project <return or object>
@node.group(name='nic', help='Node nic commands')
def node_nic():
    """Connect node an <object>"""

@node_nic.command(name='register', help='Register a nic on a node')
@click.argument('node')
@click.argument('nic')
@click.argument('macaddress')
def node_nic_register(node, nic, macaddress):
    """
    Register existence of a <nic> with the given <macaddr> on the given <node>
    """
    C.node.add_nic(node, nic, macaddress)


@node_nic.command(name='delete', help='Delete a nic from a node')
@click.argument('node')
@click.argument('nic')
def node_nic_delete(node, nic):
    """Delete a <nic> on a <node>"""
    C.node.remove_nic(node, nic)


@node_nic.command(name='show', help="Show info about a node's nic")
@click.argument('node')
@click.argument('nic')
def node_nic_show(node, nic):
    """Show info about a node's nic"""

###########################
@node.group(name='power', help='Perform node power operations')
def node_power():
    """Perform node power operations"""


@node_power.command(name='off', help="Power off node")
@click.argument('node')
def node_power_off(node):
    """Power off <node>"""
    C.node.power_off(node)

@node_power.command(name='cycle', help="Power cycle node")
@click.argument('node')
def node_power_cycle(node):
    """Power cycle <node>"""
    C.node.power_cycle(node)

###########################

@node.group(name='metadata', help='Node metadata commands')
def node_metadata():
    """Node metadata commands"""

@node_metadata.command(name='set', help='Set node metadata')
@click.argument('node')
@click.argument('label')
@click.argument('value')
def node_metadata_set(node, label, value):
    """Register metadata with <label> and <value> with <node> """
    C.node.metadata_set(node, label, value)


@node_metadata.command(name='delete', help='Delete node metadata')
@click.argument('node')
@click.argument('label')
def node_metadata_delete(node, label):
    """Delete metadata with <label> from a <node>"""
    C.node.metadata_delete(node, label)


@node.command(name='show-console', help='Show console')
@click.argument('node')
def node_show_console(node):
    """Display console log for <node>"""
    print (C.node.show_console(node))



@node.command(name='start-console', help='Start console')
@click.argument('node')
def node_start_console(node):
    """Start logging console output from <node>"""
    C.node.start_console(node)


@node.command(name='stop-console', help='Stop console')
@click.argument('node')
def node_stop_console(node):
    """Stop logging console output from <node> and delete the log"""
    C.node.stop_console(node)


####################################
### PROJECT SUBCOMMANDS GO HERE! ###
####################################

###########################
# I am invoking the project list and project list <something> commands here
# one downside of this is that the command `hil project list` will just
# complete without telling that there's more to that command. However,
# I have written in the help, that it can also invoke a subcommand.
# Alternatively, just as other subcommands, one can type
# `hil project list --help` to see what more can be done.

@project.group(name='list', invoke_without_command=True)
@click.pass_context
def project_list(ctx):
    """List all projects or invoke subcommand
    """
    if ctx.invoked_subcommand is None:
        """List all projects"""
        q = C.project.list()
        sys.stdout.write('%s Projects :    ' % len(q) + " ".join(q) + '\n')

@project_list.command(name='networks', help='List all networks that belong to a project')
@click.argument('project')
def project_list_networks(project):
    print "Project list networks "

@project_list.command(name='nodes', help='List all nodes that belong to a project')
@click.argument('project')
def project_list_nodes(project):
    """List all nodes attached to a <project>"""
    q = C.project.nodes_in(project)
    sys.stdout.write('Nodes allocated to %s:  ' % project + " ".join(q) + '\n')

###########################

@project.command(name='create')
@click.argument('project')
def project_create(project):
    """Create a new project"""
    C.project.create(project)

@project.command(name='delete')
@click.argument('project')
def project_delete(project):
    """Delete a project"""
    C.project.delete(project)

###########################
@project.group(name='connect')
def project_connect():
    """Connect project to an <object>"""

@project_connect.command(name='node')
@click.argument('project')
@click.argument('node')
def project_connect_node(project, node):
    """Connect <node> to <project>"""
    C.project.connect(project, node)

@project.group(name='detach')
def project_detach():
    """Detach a project from an <object>"""

@project_detach.command(name='node')
@click.argument('project')
@click.argument('node')
def project_detach_node(project, node):
    """Detach <node> from <project>"""
    C.project.detach(project, node)

####################################
### NETWORK SUBCOMMANDS GO HERE! ###
####################################

@network.command(name='create')
@click.argument('network')
@click.argument('owner')
@click.option('--access')
@click.option('--net_id')
def network_create(network, owner, access, net_id):
    """Create a link-layer <network>.  See docs/networks.md for details"""
    if net_id is None:
        net_id = ''
    if access is None:
        access = owner
    C.network.create(network, owner, access, net_id)


@network.command(name='delete')
@click.argument('network')
def network_delete(network):
    """Delete a <network>"""
    C.network.delete(network)


@network.command(name='show')
@click.argument('network')
def network_show(network):
    """Display information about <network>"""
    q = C.network.show(network)
    for item in q.items():
        sys.stdout.write("%s\t  :  %s\n" % (item[0], item[1]))


###########################
@network.group(name='list', invoke_without_command=True)
@click.pass_context
def network_list(ctx):
    """List all networks or invoke a subcommand"""
    if ctx.invoked_subcommand is None:
        q = C.network.list()
        for item in q.items():
            sys.stdout.write('%s \t : %s\n' % (item[0], item[1]))

@network_list.command('attachments')
@click.argument('network')
@click.argument('project')
def list_network_attachments(network, project):
    """List nodes connected to a network
    <project> may be either "all" or a specific project name.
    """
    print C.network.list_network_attachments(network, project)
###########################

@network.group(name='grant-access')
def network_grant_access():
    """Grant network access to a project"""


@network.group(name='revoke-access')
def network_revoke_access():
    """Grant network access to a project"""

@network_grant_access.command(name='project')
@click.argument('project')
@click.argument('network')
def network_grant_project_access(project, network):
    """Add <project> to <network> access"""
    C.network.grant_access(project, network)

@network_revoke_access.command(name='project')
@click.argument('project')
@click.argument('network')
def network_revoke_project_access(project, network):
    """Remove <project> from <network> access"""
    C.network.revoke_access(project, network)
###########################


def main():
    ensure_not_root()
    setup_http_client()
    try:
        cli()
    except FailedAPICallException as e:
        sys.exit('Error: %s\n' % e.message)
    except InvalidAPIArgumentsException as e:
        sys.exit('Error: %s\n' % e.message)
    except BadArgumentError as e:
        sys.exit('Error: %s\n' % e.message)
    except Exception as e:
        sys.exit('Unexpected error: %s\n' % e.message)
