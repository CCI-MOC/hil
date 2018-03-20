"""Commands related to node are in this module"""
import click
import sys
from hil.cli.client_setup import setup_http_client

C = None


@click.group()
def node():
    """Commands related to node"""
    global C
    C = setup_http_client()


@node.command(name='list')
@click.argument('free', type=click.Choice(['free', 'all']), required=True)
def nodes_list(free):
    """List all nodes or free nodes"""
    q = C.node.list(free)
    if free == 'all':
        sys.stdout.write('All nodes %s\t:    %s\n' % (len(q), " ".join(q)))
    else:
        sys.stdout.write('Free nodes %s\t:   %s\n' % (len(q), " ".join(q)))


@node.command(name='show')
@click.argument('node')
def node_show(node):
    """Show node information"""
    q = C.node.show(node)
    for item in q.items():
        sys.stdout.write("%s\t  :  %s\n" % (item[0], item[1]))


@node.command(name='bootdev', short_help="Set a node's boot device")
@click.argument('node')
@click.argument('bootdev')
def node_bootdev(node, bootdev):
    """
    Sets <node> to boot from <dev> persistently

    eg; hil node_set_bootdev dell-23 pxe
    for IPMI, dev can be set to disk, pxe, or none
    """
    C.node.set_bootdev(node, bootdev)


@node.command(name='register', short_help='Register a new node')
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


@node.command(name='delete')
@click.argument('node')
def node_delete(node):
    """Delete a node"""
    C.node.delete(node)


@node.group(name='network')
def node_network():
    """Perform node network operations"""


@node_network.command(name='connect', short_help="Connect a node to a network")
@click.argument('node')
@click.argument('network')
@click.argument('nic')
@click.argument('channel', default='', required=False)
def node_network_connect(node, network, nic, channel):
    """Connect <node> to <network> on given <nic> and <channel>"""
    print C.node.connect_network(node, nic, network, channel)


@node_network.command(name='detach', short_help="Detach node from a network")
@click.argument('node')
@click.argument('network')
@click.argument('nic')
def node_network_detach(node, network, nic):
    """Detach <node> from the given <network> on the given <nic>"""
    print C.node.detach_network(node, nic, network)


@node.group(name='nic')
def node_nic():
    """Node's nics commands"""


@node_nic.command(name='register')
@click.argument('node')
@click.argument('nic')
@click.argument('macaddress')
def node_nic_register(node, nic, macaddress):
    """
    Register existence of a <nic> with the given <macaddr> on the given <node>
    """
    C.node.add_nic(node, nic, macaddress)


@node_nic.command(name='delete')
@click.argument('node')
@click.argument('nic')
def node_nic_delete(node, nic):
    """Delete a <nic> on a <node>"""
    C.node.remove_nic(node, nic)


@node.group(name='power')
def node_power():
    """Perform node power operations"""


@node_power.command(name='off')
@click.argument('node')
def node_power_off(node):
    """Power off <node>"""
    C.node.power_off(node)


@node_power.command(name='cycle')
@click.argument('node')
def node_power_cycle(node):
    """Power cycle <node>"""
    C.node.power_cycle(node)


@node.group(name='metadata')
def node_metadata():
    """Node metadata commands"""


@node_metadata.command(name='add', short_help='Add metadata to node')
@click.argument('node')
@click.argument('label')
@click.argument('value')
def node_metadata_add(node, label, value):
    """Register metadata with <label> and <value> with <node> """
    C.node.metadata_set(node, label, value)


@node_metadata.command(name='delete', short_help='Delete node metadata')
@click.argument('node')
@click.argument('label')
def node_metadata_delete(node, label):
    """Delete metadata with <label> from a <node>"""
    C.node.metadata_delete(node, label)


@node.group(name='console')
def node_console():
    """Console related commands"""


@node_console.command(name='show', short_help='Show console')
@click.argument('node')
def node_show_console(node):
    """Display console log for <node>"""
    print(C.node.show_console(node))


@node_console.command(name='start', short_help='Start console')
@click.argument('node')
def node_start_console(node):
    """Start logging console output from <node>"""
    C.node.start_console(node)


@node_console.command(name='stop', short_help='Stop console')
@click.argument('node')
def node_stop_console(node):
    """Stop logging console output from <node> and delete the log"""
    C.node.stop_console(node)
