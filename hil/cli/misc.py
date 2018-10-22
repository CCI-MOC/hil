"""Miscellaneous commands go here"""
import click
from hil.cli.client_setup import client
from prettytable import PrettyTable
import json


@click.group(name='networking-action')
def networking_action():
    """Commands related to networking-actions"""


@networking_action.command('show')
@click.argument('status_id')
@click.option('--jsonout', is_flag=True)
def show_networking_action(status_id, jsonout):
    """Displays the status of the networking action"""
    raw_output = client.node.show_networking_action(status_id)

    if jsonout:
        json_output = json.dumps(raw_output)
        print(json_output)
        return

    net_actions_table = PrettyTable()
    net_actions_table.field_names = ['ATTRIBUTE', 'INFORMATION']

    if 'node' in raw_output:
        net_actions_table.add_row(['Node', raw_output['node']])
    if 'nic' in raw_output:
        net_actions_table.add_row(['NIC', raw_output['nic']])
    if 'new_network' in raw_output:
        net_actions_table.add_row(['New Network', raw_output['new_network']])
    if 'type' in raw_output:
        net_actions_table.add_row(['Type', raw_output['type']])
    if 'channel' in raw_output:
        net_actions_table.add_row(['Channel', raw_output['channel']])
    if 'status' in raw_output:
        net_actions_table.add_row(['Status', raw_output['status']])

    print(net_actions_table)
