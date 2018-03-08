import click
import sys
import pkg_resources

from hil.client.base import FailedAPICallException
from hil.errors import BadArgumentError
from hil.commands.util import ensure_not_root
from hil.cli import node, project, network, switch, port, user, misc

VERSION = pkg_resources.require('hil')[0].version

class InvalidAPIArgumentsException(Exception):
    """Exception indicating that the user passed invalid arguments."""

@click.group()
def cli():
    """The HIL Command line"""

commands = [node.node, project.project, network.network, switch.switch,
            port.port, user.user, misc.serve, misc.serve_networks]

for command in commands:
    cli.add_command(command)

def main():
    ensure_not_root()
    try:
        cli()
    except FailedAPICallException as e:
        sys.exit('Error: %s\n' % e.message)
    except InvalidAPIArgumentsException as e:
        sys.exit('Error: %s\n' % e.message)
    except BadArgumentError as e:
        sys.exit('Error: %s\n' % e.message)
    except Exception as e:
        sys.exit('Unexpected error: %s\n' % e.message)
