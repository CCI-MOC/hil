"""Commands related to port are in this module"""
import click
from hil.cli.client_setup import client


@click.group()
def port():
    """Commands related to port"""


@port.command(name='show')
@click.argument('switch')
@click.argument('port')
def port_show(switch, port):
    """Show what's connected to <port>"""
    print client.port.show(switch, port)


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
