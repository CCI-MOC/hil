"""This module implements the HaaS command line tool."""
from haas import config
from haas.config import cfg

import logging

import sys
import urllib
import requests

commands = {}


def cmd(f):
    """A decorator, which resgisters it's argument as a command."""
    commands[f.__name__] = f
    return f


def check_status_code(response):
    if response.status_code < 200 or response.status_code >= 300:
        sys.stderr.write('Unexpected status code: %d\n' % response.status_code)
        sys.stderr.write('Response text:\n')
        sys.stderr.write(response.text)


def object_url(typename, objname):
    url = cfg.get('client', 'endpoint') + '/'
    url += typename + '/'
    url += urllib.quote(objname)
    return url


@cmd
def serve(*args):
    """Start the HaaS API server."""
    from haas import model, api_server
    model.init_db()
    api_server.app.run(debug=True)


@cmd
def user_create(username, password, *args):
    """Create a user"""
    url = object_url('user', username)
    check_status_code(requests.put(url, data={'password': password}))


@cmd
def project_deploy(projectname):
    """Deploy a project"""
    url = object_url('project', projectname)
    check_status_code(requests.post(url))


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

    There is a script located at ${source_tree}/scripts/haas, which invokes
    this function.
    """
    logging.basicConfig(level=logging.DEBUG)
    config.load()
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        usage()
    else:
        commands[sys.argv[1]](*sys.argv[2:])
