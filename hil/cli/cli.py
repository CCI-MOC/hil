"""This module implements the HIL CLI"""
import click
import sys
import pkg_resources

from hil.client.base import FailedAPICallException
from hil.commands.util import ensure_not_root
from hil.cli import node, project, network, switch, port, user, misc

VERSION = pkg_resources.require('hil')[0].version


@click.group()
@click.version_option(version=VERSION)
def cli():
    """The HIL Command line"""


commands = [node.node, project.project, network.network, switch.switch,
            port.port, user.user, misc.networking_action]

for command in commands:
    cli.add_command(command)


def main():
    """CLI entry point"""
    ensure_not_root()
    try:
        cli()
    except FailedAPICallException as e:
        sys.exit('Error: %s\n' % e.message)
    except Exception as e:
        sys.exit('Unexpected error: %s\n' % e.message)
