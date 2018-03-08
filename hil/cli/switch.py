"""Commands related to switch are in this module"""
import click
from hil.cli.client_setup import setup_http_client

C = setup_http_client()


@click.group()
def switch():
    """Commands related to switch"""