"""Commands related to port are in this module"""
import click
from hil.cli.client_setup import setup_http_client

C = setup_http_client()


@click.group()
def port():
    """Commands related to port"""