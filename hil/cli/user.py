"""Commands related to user are in this module"""
import click
from hil.cli.client_setup import setup_http_client

C = setup_http_client()


@click.group()
def user():
    """Commands related to user"""
