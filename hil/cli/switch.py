"""Commands related to switch are in this module"""
import click
import sys
import ast
from hil.cli.client_setup import client


@click.group()
def switch():
    """Commands related to switch"""


@switch.command(name='show')
@click.argument('switch')
def node_show(switch):
    """Display information about <switch>"""
    q = client.switch.show(switch)
    for item in q.items():
        sys.stdout.write("%s\t  :  %s\n" % (item[0], item[1]))


@switch.command(name='list')
def list_switches():
    """List all switches"""
    q = client.switch.list()
    sys.stdout.write('%s switches :    ' % len(q) + " ".join(q) + '\n')


@switch.command(name='register', short_help='Register a switch')
@click.argument('switch')
@click.argument('subtype')
@click.argument('args', nargs=-1)
def switch_register(switch, subtype, args):
    """Register a switch with name <switch> and
    <subtype>, <hostname>, <username>,  <password>

    eg. hil switch_register mock03 mock mockhost01 mockuser01 mockpass01

    To make a generic switch register call, pass the arguments like:

    hil switch_register switchname subtype switchinfo
    hil switch_register dell-1 'http://example.com/schema/url' '{"foo": "bar"}'
    """
    switch_api = "http://schema.massopencloud.org/haas/v0/switches/"

    if subtype == "nexus" or subtype == "delln3000":
        if len(args) == 4:
            switchinfo = {
                "hostname": args[0],
                "username": args[1],
                "password": args[2],
                "dummy_vlan": args[3]}
            subtype = switch_api + subtype
        else:
            sys.exit('ERROR: subtype ' + subtype +
                     ' requires exactly 4 arguments\n'
                     '<hostname> <username> <password>'
                     '<dummy_vlan_no>\n')

    elif subtype == "mock" or subtype == "powerconnect55xx":
        if len(args) == 3:
            switchinfo = {"hostname": args[0],
                          "username": args[1], "password": args[2]}
            subtype = switch_api + subtype
        else:
            sys.exit('ERROR: subtype ' + subtype +
                     ' requires exactly 3 arguments\n'
                     '<hostname> <username> <password>\n')

    elif subtype == "brocade" or subtype == "dellnos9":
        if len(args) == 4:
            switchinfo = {"hostname": args[0],
                          "username": args[1], "password": args[2],
                          "interface_type": args[3]}
            subtype = switch_api + subtype
        else:
            sys.exit('ERROR: subtype ' + subtype +
                     ' requires exactly 4 arguments\n'
                     '<hostname> <username> <password> '
                     '<interface_type>\n'
                     'NOTE: interface_type refers '
                     'to the speed of the switchports\n '
                     'ex. TenGigabitEthernet, FortyGigabitEthernet, '
                     'etc.\n')
    elif subtype == "ovs":
        if len(args) == 1:
            switchinfo = {"ovs_bridge": args[0]}
            subtype = switch_api + subtype
        else:
            sys.exit('ERROR: subtype ' + subtype +
                     ' requires exactly 1 arguments\n'
                     '<ovs_bridge> \n')

    else:
        if len(args) == 0:
            sys.exit('No switchinfo provided')
        try:
            switchinfo = ast.literal_eval(args[0])
        except (ValueError, SyntaxError):
            sys.exit('Malformed switchinfo')

    client.switch.register(switch, subtype, switchinfo)


@switch.command(name='delete')
@click.argument('switch')
def switch_delete(switch):
    """Delete a <switch> """
    client.switch.delete(switch)
