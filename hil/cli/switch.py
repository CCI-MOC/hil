"""Commands related to switch are in this module"""
import click
import sys
import ast
from hil.cli.client_setup import client
from prettytable import PrettyTable
import json


@click.group()
def switch():
    """Commands related to switch"""


@switch.command(name='show')
@click.argument('switch')
@click.option('--jsonout', is_flag=True)
def switch_show(switch, jsonout):
    """Display information about <switch>"""
    raw_output = client.switch.show(switch)

    if jsonout:
        json_output = json.dumps(raw_output)
        print(json_output)
        return

    switch_table = PrettyTable()
    switch_table.field_names = ['ATTRIBUTE', 'INFORMATION']

    if 'name' in raw_output:
        switch_table.add_row(['Name', raw_output['name']])

    if 'capabilities' in raw_output:
        if not raw_output['capabilities']:
            switch_table.add_row(['Capabilities', 'None'])
        else:
            switch_table.add_row(
                ['Capabilities', raw_output['capabilities'][0]])

    if 'ports' in raw_output:
        if not raw_output['ports']:
            switch_table.add_row(['Ports', 'None'])
        else:
            switch_table.add_row(['Ports', raw_output['ports'][0].values()[0]])
            for i in range(1, len(raw_output['ports'])):
                switch_table.add_row(['', raw_output['ports'][i].values()[0]])

    print(switch_table)


@switch.command(name='list')
@click.option('--jsonout', is_flag=True)
def list_switches(jsonout):
    """List all switches"""
    raw_output = client.switch.list()

    if jsonout:
        json_output = json.dumps(raw_output)
        print(json_output)
        return

    switch_table = PrettyTable(['SWITCH LIST'])
    for switch in raw_output:
        switch_table.add_row([switch])
    print(switch_table)


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
