"""This module implements the HaaS command line tool."""
from haas import config
from haas.config import cfg

import logging
import inspect
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
def serve():
    """Start the HaaS API server."""
    from haas import model, server
    model.init_db()
    server.app.run(debug=True)


@cmd
def user_create(username, password):
    """Create a user <username> with password <password>."""
    url = object_url('user', username)
    check_status_code(requests.put(url, data={'password': password}))


@cmd
def group_add_user(group, user):
    """Add <user> to <group>."""
    url = object_url('group', group) + '/add_user'
    check_status_code(requests.post(url, data={'user': user}))


@cmd
def group_remove_user(group, user):
    """Remove <user> from <group>."""
    url = object_url('group', group) + '/remove_user'
    check_status_code(requests.post(url, data={'user': user}))


@cmd
def user_delete(user):
    url = object_url('user', user)
    check_status_code(requests.delete(url))


@cmd
def group_create(groupname):
    """Create a group"""
    url = object_url('group', groupname)
    check_status_code(requests.put(url))


@cmd
def group_delete(groupname):
    """Delete a group"""
    url = object_url('group', groupname)
    check_status_code(requests.delete(url))


def project_deploy(project):
    """Deploy <project>"""
    url = object_url('project', project) + '/deploy'
    check_status_code(requests.post(url))


@cmd
def project_connect_node(projectname, nodename):
    """Connect a node to a project"""
    url = object_url('project', projectname) + '/connect_node'
    check_stats_code(requests.post(url, data={'node': nodename}))

@cmd
def project_detach_node(projectname, nodename):
    """Detach a node from a project"""
    url = object_url('project', projectname) + '/detach_node'
    check_stats_code(requests.post(url, data={'node': nodename}))

def node_register(node):
    """Register a node named <node>"""
    url = object_url('node', node)
    check_status_code(requests.put(url))


@cmd
def headnode_create_hnic(headnode, hnic, macaddr):
    """Create a NIC with the given MAC address on the given headnode"""
    url = object_url('hnic', hnic)
    check_status_code(requests.put(url, data={'headnode':headnode,
                                              'macaddr':macaddr}))

@cmd
def headnode_delete_hnic(hnic):
    """Delete a NIC on a headnode"""
    url = object_url('hnic', hnic)
    check_status_code(requests.delte(url))


def usage():
    """Display a summary of the arguments accepted by the CLI."""
    sys.stderr.write('Usage: %s <command>\n\n' % sys.argv[0])
    sys.stderr.write('Where <command> is one of:\n\n')
    for name in commands.keys():
        # For each command, print out a summary including the name, arguments,
        # and the docstring (as a #comment).
        func = commands[name]
        args, _, _, _ = inspect.getargspec(func)
        args = map(lambda name: '<%s>' % name, args)
        sys.stderr.write('    %s %s # %s\n' % (name, ' '.join(args), func.__doc__))


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

