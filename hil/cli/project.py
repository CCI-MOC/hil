"""Commands related to projects are in this module"""
import click
import time
import sys
from hil.cli.client_setup import client
from hil.cli.helper import print_json, make_table, HIL_TIMEOUT


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

    print(make_table(field_names=['Projects'],
                     rows=[[i] for i in raw_output]))


@project.command(name='list-networks')
@click.argument('project')
@click.option('--json', 'jsonout', is_flag=True)
def project_list_networks(project, jsonout):
    """List all networks attached to a <project>"""
    raw_output = client.project.networks_in(project)

    if jsonout:
        print_json(raw_output)

    print(make_table(field_names=['Networks'],
                     rows=[[i] for i in raw_output]))


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

    print(make_table(field_names=['Nodes'],
                     rows=[[i] for i in raw_output]))


@project_node.command(name='add')
@click.argument('project')
@click.argument('node')
def project_connect_node(project, node):
    """Add <node> to <project>"""
    client.project.connect(project, node)


@project_node.command(name='remove')
@click.argument('project')
@click.argument('node')
@click.option('--force', is_flag=True)
def project_detach_node(project, node, force):
    """Remove <node> from <project>"""
    if force:
        client.node.disable_obm(node)
        print("Disabled OBM")
        node_info = client.node.show(node)
        statuses = []
        if 'nics' in node_info:
            for n in node_info['nics']:
                # if any nic is connected to a network, then it has a switch
                # and port. So call revert port on those.
                if 'networks' in n:
                    try:
                        response = client.port.port_revert(
                                                    n['switch'], n['port'])
                        statuses.append(response['status_id'])
                    except KeyError:
                        print("Only admins can force remove nodes.")
                        sys.exit(1)

        done = False
        end_time = time.time() + HIL_TIMEOUT
        while not done:
            if time.time() > end_time:
                raise Exception("Removing networks is taking too long. "
                                "Set HIL_TIMEOUT to wait longer")
            done = True
            for status_id in statuses:
                response = client.node.show_networking_action(status_id)
                if response['status'] == 'ERROR':
                    print("Revert port failed. Check HIL network server")
                    return
                elif response['status'] == 'PENDING':
                    done = False
                    break
        print("Succesfuly finished removing all networks from the node.")

    client.project.detach(project, node)
