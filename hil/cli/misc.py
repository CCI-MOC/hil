"""Miscellaneous commands go here"""
import click
from hil.cli.client_setup import setup_http_client

C = None


@click.group(name='networking-action')
def networking_action():
    """Commands related to networking-actions"""
    global C
    C = setup_http_client()


@networking_action.command('show')
@click.argument('status_id')
def show_networking_action(status_id):
    """Displays the status of the networking action"""
    print C.node.show_networking_action(status_id)
