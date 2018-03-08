"""Commands related to switch are in this module"""
import click
import sys
from hil.cli.client_setup import setup_http_client

C = setup_http_client()


@click.group()
def switch():
    """Commands related to switch"""


@switch.command(name='show', help='Show switch information')
@click.argument('switch')
def node_show(switch):
    """Display information about <switch>"""
    q = C.switch.show(switch)
    for item in q.items():
        sys.stdout.write("%s\t  :  %s\n" % (item[0], item[1]))


@switch.command(name='list', help='List all switches')
def list_switches():
    """List all switches"""
    q = C.switch.list()
    sys.stdout.write('%s switches :    ' % len(q) + " ".join(q) + '\n')


@switch.command(name='register', help='Register a switch')
@click.argument('switch')
@click.argument('subtype')
@click.argument('args', nargs=-1)
def switch_register(switch, subtype, args):
    """Register a switch with name <switch> and <subtype> <args>
    eg. hil switch_register mock03 mock mockhost01 mockuser01 mockpass01
    """
    # hopefullt the switch_register client call will be done before the cli.the
    # args is a tuple that can have unlimited number of arguments.
    pass


@switch.command(name='delete', help='Delete a switch')
def switch_delete(switch):
    """Delete a <switch> """
    C.switch.delete(switch)
