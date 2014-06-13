"""This module implements the HaaS command line tool."""
from haas import config
from haas.config import cfg

import sys
import urllib
import requests

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
    api_server.app.run(debug=True)

@cmd
def user_create(username, password, *args):
    """Create a user"""
    url = cfg.get('client', 'endpoint') + '/user/' + urllib.quote(username, safe='')
    r = requests.put(url, data={'password': password})
    if r.status_code < 200 or r.status_code >= 300:
        sys.stderr.write('Unexpected status code: %d\n' % r.status_code)
        sys.stderr.write('Response text:\n')
        sys.stderr.write(r.text)

def usage():
    """Display a summary of the arguments accepted by the CLI."""
    # TODO: We should fetch the arguments and include them in the message
    # somehow.
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
        commands[sys.argv[1]](*sys.argv[2:])
