"""Commands related to networks are in this module"""
import click
import sys
from hil.cli.client_setup import setup_http_client

C = None


@click.group()
def network():
    """Commands related to network"""
    global C
    C = setup_http_client()


@network.command(name='create', short_help='Create a new network')
@click.argument('network')
@click.argument('owner')
@click.option('--access')
@click.option('--net_id')
def network_create(network, owner, access, net_id):
    """Create a link-layer <network>.  See docs/networks.md for details"""
    if net_id is None:
        net_id = ''
    if access is None:
        access = owner
    C.network.create(network, owner, access, net_id)


@network.command(name='delete')
@click.argument('network')
def network_delete(network):
    """Delete a network"""
    C.network.delete(network)


@network.command(name='show')
@click.argument('network')
def network_show(network):
    """Display information about network"""
    q = C.network.show(network)
    for item in q.items():
        sys.stdout.write("%s\t  :  %s\n" % (item[0], item[1]))


@network.command(name='list')
def network_list():
    """List all networks"""
    q = C.network.list()
    for item in q.items():
        sys.stdout.write('%s \t : %s\n' % (item[0], item[1]))


@network.group(name='project')
def network_project():
    """Commands that manipulate project and network relations"""


@network_project.command('list')
@click.argument('network')
@click.option('--project')
def list_network_attachments(network, project):
    """Lists all the attachments from <project> for <network>

    If <project> is `None`, lists all attachments for <network>
    """
    print C.network.list_network_attachments(network, project)


@network_project.command(name='add')
@click.argument('network')
@click.argument('project')
def network_grant_project_access(project, network):
    """Add <project> to <network> access"""
    C.network.grant_access(project, network)


@network_project.command(name='remove')
@click.argument('network')
@click.argument('project')
def network_revoke_project_access(project, network):
    """Remove <project> from <network> access"""
    C.network.revoke_access(project, network)
