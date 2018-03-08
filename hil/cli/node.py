"""Commands related to node are in this module"""
import click
import sys
from hil.cli.client_setup import setup_http_client

C = setup_http_client()


@click.group()
def node():
    """Commands related to node"""

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


###########################
# I am doing the dash thing with the console commands. Let me know what's
# preffered, should I go the nic commands route, or the network commands route.

@node.command(name='show-console', help='Show console')
@click.argument('node')
def node_show_console(node):
    """Display console log for <node>"""
    # Should be simple to implement in the client library for now.
    C.node.show_console(node)


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

