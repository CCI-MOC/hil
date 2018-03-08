"""Commands related to projects are in this module"""
import click
import sys
from hil.cli.client_setup import setup_http_client

C = setup_http_client()


@click.group()
def project():
    """Commands related to project"""


@project.command(name='create')
@click.argument('project')
def project_create(project):
    """Create a new project"""
    C.project.create(project)


@project.command(name='delete')
@click.argument('project')
def project_delete(project):
    """Delete a project"""
    C.project.delete(project)


@project.command(name='list')
def project_list():
    """List all projects"""
    q = C.project.list()
    sys.stdout.write('%s Projects :    ' % len(q) + " ".join(q) + '\n')


@project.group(name='network')
def project_network():
    """Project and network related operations"""


@project_network.command(name='list')
@click.argument('project')
def project_list_networks(project):
    """List all networks attached to a <project>"""
    q = C.project.networks_in(project)
    sys.stdout.write(
            "Networks allocated to %s\t:   %s\n" % (project, " ".join(q))
            )


@project.group(name='node')
def project_node():
    """Project and node related operations"""


@project_node.command(name='list')
@click.argument('project')
def project_node_list(project):
    """List all nodes attached to a <project>"""
    q = C.project.nodes_in(project)
    sys.stdout.write('Nodes allocated to %s:  ' % project + " ".join(q) + '\n')


@project_node.command(name='add')
@click.argument('project')
@click.argument('node')
def project_connect_node(project, node):
    """Add <node> to <project>"""
    C.project.connect(project, node)


@project_node.command(name='remove')
@click.argument('project')
@click.argument('node')
def project_detach_node(project, node):
    """Remove <node> from <project>"""
    C.project.detach(project, node)
