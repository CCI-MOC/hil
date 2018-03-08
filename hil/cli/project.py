import click
import sys
from hil.cli.client_setup import setup_http_client

C = setup_http_client()


@click.group()
def project():
    """Commands related to project"""

####################################
### PROJECT SUBCOMMANDS GO HERE! ###
####################################

###########################
# I am invoking the project list and project list <something> commands here
# one downside of this is that the command `hil project list` will just
# complete without telling that there's more to that command. However,
# I have written in the help, that it can also invoke a subcommand.
# Alternatively, just as other subcommands, one can type
# `hil project list --help` to see what more can be done.

@project.group(name='list', invoke_without_command=True)
@click.pass_context
def project_list(ctx):
    """List all projects or invoke subcommand
    """
    if ctx.invoked_subcommand is None:
        """List all projects"""
        q = C.project.list()
        sys.stdout.write('%s Projects :    ' % len(q) + " ".join(q) + '\n')

@project_list.command(name='networks', help='List all networks that belong to a project')
@click.argument('project')
def project_list_networks(project):
    print "Project list networks "

@project_list.command(name='nodes', help='List all nodes that belong to a project')
@click.argument('project')
def project_list_nodes(project):
    """List all nodes attached to a <project>"""
    q = C.project.nodes_in(project)
    sys.stdout.write('Nodes allocated to %s:  ' % project + " ".join(q) + '\n')

###########################

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

###########################
@project.group(name='connect')
def project_connect():
    """Connect project to an <object>"""

@project_connect.command(name='node')
@click.argument('project')
@click.argument('node')
def project_connect_node(project, node):
    """Connect <node> to <project>"""
    C.project.connect(project, node)

@project.group(name='detach')
def project_detach():
    """Detach a project from an <object>"""

@project_detach.command(name='node')
@click.argument('project')
@click.argument('node')
def project_detach_node(project, node):
    """Detach <node> from <project>"""
    C.project.detach(project, node)