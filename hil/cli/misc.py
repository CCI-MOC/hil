"""Miscellaneous commands go here"""
import click
from hil.cli.client_setup import setup_http_client

C = setup_http_client()


@click.group(name='networking-action')
def networking_action():
    """Commands related to networking-actions"""


@networking_action.command('show')
@click.argument('status_id')
def show_networking_action(status_id):
    """Displays the status of the networking action"""
    print C.node.show_networking_action(status_id)
