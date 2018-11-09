"""Commands related to projects are in this module"""
import click
import sys
from prettytable import PrettyTable
from hil.cli.client_setup import client
from hil.cli.helper import print_json, print_list_table


@click.group()
def project():
    """Commands related to project"""


@project.command(name='create')
@click.argument('project')
def project_create(project):
    """Create a new project"""
    client.project.create(project)


@project.command(name='delete')
@click.argument('project')
def project_delete(project):
    """Delete a project"""
    client.project.delete(project)


@project.command(name='list')
@click.option('--json', 'jsonout', is_flag=True)
def project_list(jsonout):
    """List all projects"""
    raw_output = client.project.list()

    if jsonout:
        print_json(raw_output)

    print_list_table(raw_output, 'Projects')


@project.command(name='list-networks')
@click.argument('project')
@click.option('--json', 'jsonout', is_flag=True)
def project_list_networks(project, jsonout):
    """List all networks attached to a <project>"""
    raw_output = client.project.networks_in(project)

    if jsonout:
        print_json(raw_output)

    print_list_table(raw_output, 'Networks')


@project.group(name='node')
def project_node():
    """Project and node related operations"""


@project_node.command(name='list')
@click.argument('project')
@click.option('--json', 'jsonout', is_flag=True)
def project_node_list(project, jsonout):
    """List all nodes attached to a <project>"""
    raw_output = client.project.nodes_in(project)

    if jsonout:
        print_json(raw_output)

    print_list_table(raw_output, 'Nodes')


@project_node.command(name='add')
@click.argument('project')
@click.argument('node')
def project_connect_node(project, node):
    """Add <node> to <project>"""
    client.project.connect(project, node)


@project_node.command(name='remove')
@click.argument('project')
@click.argument('node')
def project_detach_node(project, node):
    """Remove <node> from <project>"""
    client.project.detach(project, node)
