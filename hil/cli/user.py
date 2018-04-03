"""Commands related to user are in this module"""
import click
from hil.cli.client_setup import client


@click.group()
def user():
    """Commands related to user"""


@user.command(name='create', short_help='Create a new user')
@click.argument('username')
@click.argument('password')
@click.argument('is_admin', type=click.Choice(['admin', 'regular']))
def user_create(username, password, is_admin):
    """Create a user <username> with password <password>.

    <is_admin> may be either "admin" or "regular", and determines whether
    the user has administrative privileges.
    """
    client.user.create(username, password, is_admin == 'admin')


@user.command(name='delete')
@click.argument('username')
def user_delete(username):
    """Delete the user <username>"""
    client.user.delete(username)


@user.group(name='project')
def user_project():
    """add/remove users from project"""


@user_project.command('add')
@click.argument('user')
@click.argument('project')
def user_add_project(user, project):
    """Add <user> to <project>"""
    client.user.add(user, project)


@user_project.command('remove')
@click.argument('user')
@click.argument('project')
def user_remove_project(user, project):
    """Remove <user> from <project>"""
    client.user.remove(user, project)


@user.command(name='set-admin')
@click.argument('username')
@click.argument('is_admin', type=click.Choice(['admin', 'regular']))
def user_set_admin(username, is_admin):
    """Changes the admin status of user <username>.

    <is_admin> may by either "admin" or "regular", and determines whether
    a user is authorized for administrative privileges.
    """
    client.user.set_admin(username, is_admin == 'admin')
