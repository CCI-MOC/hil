"""Commands related to port are in this module"""
import click
from hil.cli.client_setup import client
from prettytable import PrettyTable
import json


@click.group()
def port():
    """Commands related to port"""


@port.command(name='show')
@click.argument('switch')
@click.argument('port')
@click.option('--jsonout', is_flag=True)
def port_show(switch, port, jsonout):
    """Show what's connected to <port>"""

    raw_output = client.port.show(switch, port)

    if jsonout:
        json_output = json.dumps(raw_output)
        print(json_output)
        return

    port_table = PrettyTable()
    port_table.field_names = ['ATTRIBUTE', 'INFORMATION']

    if 'node' in raw_output:
        port_table.add_row(['Node', raw_output['node']])
    if 'nic' in raw_output:
        port_table.add_row(['NIC', raw_output['nic']])
    if 'networks' in raw_output:
        port_table.add_row(['Networks', raw_output['networks'].values()[0] +
                            '(' + raw_output['networks'].keys()[0] + ')'])

    print(port_table)


@port.command(name='register')
@click.argument('switch')
@click.argument('port')
def port_register(switch, port):
    """Register a <port> with <switch> """
    client.port.register(switch, port)


@port.command(name='delete')
@click.argument('switch')
@click.argument('port')
def port_delete(switch, port):
    """Delete a <port> from a <switch>"""
    client.port.delete(switch, port)


@port.command(name='revert')
@click.argument('switch')
@click.argument('port')
def port_revert(switch, port):
    """Detach a <port> on a <switch> from all attached networks."""
    print client.port.port_revert(switch, port)


@port.group(name='nic')
def port_nic():
    """Operations affecting a port and a nic"""


@port_nic.command(name='add')
@click.argument('switch')
@click.argument('port')
@click.argument('node')
@click.argument('nic')
def port_nic_add(switch, port, node, nic):
    """Connect a <port> on a <switch> to a <nic> on a <node>"""
    client.port.connect_nic(switch, port, node, nic)


@port_nic.command(name='remove')
@click.argument('switch')
@click.argument('port')
def port_nic_remove(switch, port):
    """Detach a <port> on a <switch> from whatever's connected to it"""
    client.port.detach_nic(switch, port)
