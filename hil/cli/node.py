"""Commands related to node are in this module"""
import click
import sys
from hil.cli.client_setup import client
from prettytable import PrettyTable
import json


@click.group()
def node():
    """Commands related to node"""


@node.command(name='list')
@click.argument('pool', type=click.Choice(['free', 'all']), required=True)
@click.option('--jsonout', is_flag=True)
def nodes_list(pool, jsonout):
    """List all nodes or free nodes"""
    raw_output = client.node.list(pool)

    if jsonout:
        json_output = json.dumps(raw_output)
        print(json_output)
        return

    node_list = PrettyTable(['NODE LIST'])
    for node in raw_output:
        node_list.add_row([node])
    print(node_list)


@node.command(name='show')
@click.argument('node')
@click.option('--jsonout', is_flag=True)
def node_show(node, jsonout):
    """Show node information"""
    raw_output = client.node.show(node)
    node_table = PrettyTable()

    if jsonout:
        json_output = json.dumps(raw_output)
        print(json_output)
        return

    node_table.field_names = ['ATTRIBUTE', 'INFORMATION']

    if 'project' in raw_output:
        node_table.add_row(['Project', raw_output['project']])
    if 'name' in raw_output:
        node_table.add_row(['Name', raw_output['name']])
        node_table.add_row(['', ''])
    if 'nics' in raw_output:
        for n in raw_output['nics']:
            if 'label' in n:
                node_table.add_row(['Label', n['label']])
            if 'macaddr' in n:
                node_table.add_row(['Macaddr', n['macaddr']])
            if 'switch' in n:
                node_table.add_row(['Switch', n['switch']])
            if 'port' in n:
                node_table.add_row(['Port', n['port']])
            if 'networks' in n:
                if not n['networks']:
                    node_table.add_row(['Networks', 'None'])
                else:
                    info = n['networks'].values()[0] + \
                        '(' + n['networks'].keys()[0] + ')'
                    node_table.add_row(['Networks', info])
                    if len(n['networks']) > 1:
                        for i in range(1, len(n['networks'])):
                            info = n['networks'].values()[i] + \
                                '(' + n['networks'].keys()[i] + ')'
                            node_table.add_row(['', info])
                node_table.add_row(['', ''])
        if 'metadata' in raw_output:
            for key, val in raw_output['metadata'].items():
                node_table.add_row([key, val.strip('""')])

    print(node_table)


@node.command(name='bootdev', short_help="Set a node's boot device")
@click.argument('node')
@click.argument('bootdev')
def node_bootdev(node, bootdev):
    """
    Sets <node> to boot from <dev> persistently

    eg; hil node_set_bootdev dell-23 pxe
    for IPMI, dev can be set to disk, pxe, or none
    """
    client.node.set_bootdev(node, bootdev)


@node.command(name='register', short_help='Register a new node')
@click.argument('node')
@click.argument('obmd-uri')
@click.argument('obmd-admin-token')
def node_register(node,
                  obmd_uri,
                  obmd_admin_token):
    """Register a node named <node>"""
    client.node.register(
        node,
        obmd_uri,
        obmd_admin_token,
    )


@node.command(name='delete')
@click.argument('node')
def node_delete(node):
    """Delete a node"""
    client.node.delete(node)


@node.group(name='network')
def node_network():
    """Perform node network operations"""


@node_network.command(name='connect', short_help="Connect a node to a network")
@click.argument('node')
@click.argument('nic')
@click.argument('network')
@click.argument('channel', default='', required=False)
def node_network_connect(node, network, nic, channel):
    """Connect <node> to <network> on given <nic> and <channel>"""
    print(client.node.connect_network(node, nic, network, channel))


@node_network.command(name='detach', short_help="Detach node from a network")
@click.argument('node')
@click.argument('nic')
@click.argument('network')
def node_network_detach(node, network, nic):
    """Detach <node> from the given <network> on the given <nic>"""
    print(client.node.detach_network(node, nic, network))


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
    client.node.add_nic(node, nic, macaddress)


@node_nic.command(name='delete')
@click.argument('node')
@click.argument('nic')
def node_nic_delete(node, nic):
    """Delete a <nic> on a <node>"""
    client.node.remove_nic(node, nic)


@node.group(name='obm')
def obm():
    """Commands related to obm configuration"""


@obm.command()
@click.argument('node')
def enable(node):
    """Enable <node>'s obm"""
    client.node.enable_obm(node)


@obm.command()
@click.argument('node')
def disable(node):
    """Disable <node>'s obm"""
    client.node.disable_obm(node)


@node.group(name='power')
def node_power():
    """Perform node power operations"""


@node_power.command(name='off')
@click.argument('node')
def node_power_off(node):
    """Power off <node>"""
    client.node.power_off(node)


@node_power.command(name='on')
@click.argument('node')
def node_power_on(node):
    """Power on <node>"""
    client.node.power_on(node)


@node_power.command(name='cycle')
@click.argument('node')
def node_power_cycle(node):
    """Power cycle <node>"""
    client.node.power_cycle(node)


@node_power.command(name='status')
@click.argument('node')
def node_power_status(node):
    """Returns node power status"""
    print(client.node.power_status(node))


@node.group(name='metadata')
def node_metadata():
    """Node metadata commands"""


@node_metadata.command(name='add', short_help='Add metadata to node')
@click.argument('node')
@click.argument('label')
@click.argument('value')
def node_metadata_add(node, label, value):
    """Register metadata with <label> and <value> with <node> """
    client.node.metadata_set(node, label, value)


@node_metadata.command(name='delete', short_help='Delete node metadata')
@click.argument('node')
@click.argument('label')
def node_metadata_delete(node, label):
    """Delete metadata with <label> from a <node>"""
    client.node.metadata_delete(node, label)


@node.group(name='console')
def node_console():
    """Console related commands"""


@node_console.command(name='show', short_help='Show console')
@click.argument('node')
def node_show_console(node):
    """Display console log for <node>

    This will stream data from the console to standard output; press
    Ctrl+C to stop.
    """
    try:
        for data in client.node.show_console(node):
            sys.stdout.write(data)
    except KeyboardInterrupt:
        pass
