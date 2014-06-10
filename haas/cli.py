"""This module implements the HaaS command line tool."""
from haas import config

import sys

commands = {}

def cmd(f):
    """A decorator, which resgisters it's argument as a command."""
    commands[f.__name__] = f
    return f

@cmd
def serve(*args):
    """Start the HaaS API server."""
    from haas import model, api_server
    model.init_db()
    api_server.app.run()

def usage():
    sys.stderr.write('Usage: %s <command> <args...>\n\n' % sys.argv[0])
    sys.stderr.write('Where <command> is one of:\n\n')
    for name in commands.keys():
        sys.stderr.write('    %s # %s\n' % (name, commands[name].__doc__))

def main():
    """Entry point to the CLI.
    
    There is a script located at ${source_tree}/scripts/haas, which invokes this
    function.
    """
    config.load()
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        usage()
    else:
        commands[sys.argv[1]](sys.argv[2:])
