"""Commands related to networks are in this module"""
import click
import sys
from hil.cli.client_setup import setup_http_client

C = setup_http_client()


@click.group()
def network():
    """Commands related to network"""

####################################
### NETWORK SUBCOMMANDS GO HERE! ###
####################################

@network.command(name='create')
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
    """Delete a <network>"""
    C.network.delete(network)


@network.command(name='show')
@click.argument('network')
def network_show(network):
    """Display information about <network>"""
    q = C.network.show(network)
    for item in q.items():
        sys.stdout.write("%s\t  :  %s\n" % (item[0], item[1]))


###########################
@network.group(name='list', invoke_without_command=True)
@click.pass_context
def network_list(ctx):
    """List all networks or invoke a subcommand"""
    if ctx.invoked_subcommand is None:
        q = C.network.list()
        for item in q.items():
            sys.stdout.write('%s \t : %s\n' % (item[0], item[1]))

@network_list.command('attachments')
@click.argument('network')
@click.argument('project')
def list_network_attachments(network, project):
    """List nodes connected to a network
    <project> may be either "all" or a specific project name.
    """
    print C.network.list_network_attachments(network, project)
###########################

@network.group(name='grant-access')
def network_grant_access():
    """Grant network access to a project"""


@network.group(name='revoke-access')
def network_revoke_access():
    """Grant network access to a project"""

@network_grant_access.command(name='project')
@click.argument('project')
@click.argument('network')
def network_grant_project_access(project, network):
    """Add <project> to <network> access"""
    C.network.grant_access(project, network)

@network_revoke_access.command(name='project')
@click.argument('project')
@click.argument('network')
def network_revoke_project_access(project, network):
    """Remove <project> from <network> access"""
    C.network.revoke_access(project, network)
