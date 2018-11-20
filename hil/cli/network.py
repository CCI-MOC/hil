"""Commands related to networks are in this module"""
import click
from prettytable import PrettyTable
from hil.cli.client_setup import client
from hil.cli.helper import print_json, make_table


@click.group()
def network():
    """Commands related to network"""


@network.command(name='create', short_help='Create a new network')
@click.argument('network')
@click.argument('owner')
@click.option('--access', help='Projects that can access this network. '
              'Defaults to the owner of the network')
@click.option('--net-id',
              help='Network ID for network. Only admins can specify this.')
def network_create(network, owner, access, net_id):
    """Create a link-layer <network>.  See docs/networks.md for details"""
    if net_id is None:
        net_id = ''
    if access is None:
        access = owner
    client.network.create(network, owner, access, net_id)


@network.command(name='delete')
@click.argument('network')
def network_delete(network):
    """Delete a network"""
    client.network.delete(network)


@network.command(name='show')
@click.argument('network')
@click.option('--json', 'jsonout', is_flag=True)
def network_show(network, jsonout):
    """Display information about network"""
    raw_output = client.network.show(network)

    if jsonout:
        print_json(raw_output)

    # Collect raw output into presentable form
    channels = '\n'.join(raw_output['channels']) + '\n'
    projects = '\n'.join(raw_output['access']) + '\n'

    nodes = [node + '(' + ','.join(nics) + ')'
             for node, nics in raw_output['connected-nodes'].iteritems()]

    print(make_table(field_names=['Field', 'Value'],
                     rows=[['Name', raw_output['name']],
                           ['Owner', raw_output['owner']],
                           ['Channels', channels],
                           ['Access', projects],
                           ['Connected Nodes', '\n'.join(nodes)]
                           ]))


@network.command(name='list')
@click.option('--json', 'jsonout', is_flag=True)
def network_list(jsonout):
    """List all networks"""
    raw_output = client.network.list()

    if jsonout:
        print_json(raw_output)

    rows = [[name, attributes['network_id'],
             ','.join(attributes['projects'])]
            for name, attributes in raw_output.iteritems()]

    table = make_table(
        field_names=['Name', 'Network ID', 'Projects'], rows=rows)
    table.sortby = 'Name'
    print(table)


@network.command('list-attachments')
@click.argument('network')
@click.option('--project', help='Name of project.')
@click.option('--json', 'jsonout', is_flag=True)
def list_network_attachments(network, project, jsonout):
    """Lists all the attachments from <project> for <network>

    If <project> is `None`, lists all attachments for <network>
    """
    # Client library expects us to send it a 'all' instead of nothing.
    if project is None:
        project = 'all'

    raw_output = client.network.list_network_attachments(network, project)

    if jsonout:
        print_json(raw_output)

    rows = [[node, attributes['project'],
             attributes['nic'], attributes['channel']]
            for node, attributes in raw_output.iteritems()]

    print(make_table(field_names=['Node', 'Project', 'Nic', 'Channel'],
                     rows=rows))


@network.command(name='grant-access')
@click.argument('network')
@click.argument('project')
def network_grant_project_access(project, network):
    """Add <project> to <network> access"""
    client.network.grant_access(project, network)


@network.command(name='revoke-access')
@click.argument('network')
@click.argument('project')
def network_revoke_project_access(project, network):
    """Remove <project> from <network> access"""
    client.network.revoke_access(project, network)
