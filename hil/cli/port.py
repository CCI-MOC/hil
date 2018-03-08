"""Commands related to port are in this module"""
import click
from hil.cli.client_setup import setup_http_client

C = setup_http_client()


@click.group()
def port():
    """Commands related to port"""


@port.command(name='show', help='Show port information')
@click.argument('switch')
@click.argument('port')
def port_show(switch, port):
    """Show what's connected to <port>"""
    print C.port.show(switch, port)


@port.command(name='register', help="Register new port on a switch")
@click.argument('switch')
@click.argument('port')
def port_register(switch, port):
    """Register a <port> with <switch> """
    C.port.register(switch, port)


@port.command(name='delete', help="Delete port from a switch")
@click.argument('switch')
@click.argument('port')
def port_delete(switch, port):
    """Delete a <port> from a <switch>"""
    C.port.delete(switch, port)


@port.command(name='revert', help="Remove all networks from a port")
@click.argument('switch')
@click.argument('port')
def port_revert(switch, port):
    """Detach a <port> on a <switch> from all attached networks."""
    print C.port.port_revert(switch, port)


@port.group(name='nic', help="Operations affecting a port and a nic")
def port_nic():
    """Operations affecting a port and a nic"""


@port_nic.command(name='add')
@click.argument('switch')
@click.argument('port')
@click.argument('node')
@click.argument('nic')
def port_nic_add(switch, port, node, nic):
    """Connect a <port> on a <switch> to a <nic> on a <node>"""
    C.port.connect_nic(switch, port, node, nic)


@port_nic.command(name='remove')
@click.argument('switch')
@click.argument('port')
def port_nic_remove(switch, port):
    """Detach a <port> on a <switch> from whatever's connected to it"""
    C.port.detach_nic(switch, port)
