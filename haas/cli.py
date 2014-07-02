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

# TODO: This function's name is no longer very accurate.  As soon as it is
# safe, we should change it to something more generic.
def object_url(*args):
    url = cfg.get('client', 'endpoint')
    for arg in args:
        url += '/' + urllib.quote(arg)
    return url


@cmd
def serve():
    """Start the HaaS API server."""
    from haas import model, server
    model.init_db()
    server.app.run(debug=True)

@cmd
def init_db():
    """Initialize the database"""
    from haas import model
    model.init_db(create=True)


@cmd
def user_create(username, password):
    """Create a user <username> with password <password>."""
    url = object_url('user', username)
    check_status_code(requests.put(url, data={'password': password}))

@cmd
def network_create(network, group):
    """Create a <network> belonging to a <group>"""
    url = object_url('network', network)
    check_status_code(requests.put(url, data={'group': group}))

@cmd
def network_delete(network):
    """Delete a <network>"""
    url = object_url('network', network)
    check_status_code(requests.delete(url))

    
@cmd
def user_delete(username):
    url = object_url('user', username)
    check_status_code(requests.delete(url))


@cmd
def group_add_user(group, user):
    """Add <user> to <group>."""
    url = object_url('group', group, 'add_user')
    check_status_code(requests.post(url, data={'user': user}))


@cmd
def group_remove_user(group, user):
    """Remove <user> from <group>."""
    url = object_url('group', group, 'remove_user')
    check_status_code(requests.post(url, data={'user': user}))

@cmd
def project_create(projectname, group, *args):
    """Create a project"""
    url = object_url('project', projectname)
    check_status_code(requests.put(url, data={'group': group}))

@cmd
def project_delete(projectname):
    url = object_url('project', projectname)
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
    url = object_url('project', project, 'deploy')
    check_status_code(requests.post(url))


@cmd
def headnode_create(hn_name, group):
    """Create a headnode <hn_name> belonging to <group>"""
    url = object_url('headnode', hn_name)
    check_status_code(requests.put(url, data={'group': group}))

@cmd
def headnode_delete(hn_name):
    """Delete the headnode <hn_name>"""
    url = object_url('headnode', hn_name)
    check_status_code(requests.delete(url))

@cmd
def project_connect_node(project, node):
    """Connect <node> to <project>"""
    url = object_url('project', project, 'connect_node')
    check_status_code(requests.post(url, data={'node': node}))

@cmd
def project_detach_node(project, node):
    """Detach <node> from <project>"""
    url = object_url('project', project, 'detach_node')
    check_status_code(requests.post(url, data={'node': node}))

@cmd
def project_connect_headnode(project, headnode):
    """Connect <headnode> to <project>"""
    url = object_url('project', project, 'connect_headnode')
    check_status_code(requests.post(url, data={'headnode': headnode}))

@cmd
def project_detach_headnode(project, headnode):
    """Detach <headnode> from <project>"""
    url = object_url('project', project, 'detach_headnode')
    check_status_code(requests.post(url, data={'headnode': headnode}))

@cmd
def project_connect_network(project, network):
    """Connect <network> to <project>"""
    url = object_url('project', project, 'connect_network')
    check_status_code(requests.post(url, data={'network': network}))

@cmd
def project_detach_network(project, network):
    """Detach <network> from <project>"""
    url = object_url('project', project, 'detach_network')
    check_status_code(requests.post(url, data={'network': network}))

@cmd
def node_register(node):
    """Register a node named <node>"""
    url = object_url('node', node)
    check_status_code(requests.put(url))

@cmd
def node_register_nic(node, nic, macaddr):
    """Register existence of a NIC with the given MAC address on the given node"""
    url = object_url('node', node, 'nic', nic)
    check_status_code(requests.put(url, data={'macaddr':macaddr}))

@cmd
def node_delete_nic(node, nic):
    """Delete a NIC on a node"""
    url = object_url('node', node, 'nic', nic)
    check_status_code(requests.delete(url))

@cmd
def headnode_create_hnic(headnode, hnic, macaddr):
    """Create a NIC with the given MAC address on the given headnode"""
    url = object_url('headnode', headnode, 'hnic', hnic)
    check_status_code(requests.put(url, data={'macaddr':macaddr}))

@cmd
def headnode_delete_hnic(headnode, hnic):
    """Delete a NIC on a headnode"""
    url = object_url('headnode', headnode, 'hnic', hnic)
    check_status_code(requests.delete(url))

@cmd
def vlan_register(vlan_id):
    """Register existence of VLAN number <vlan_id>"""
    url = object_url('vlan', vlan_id)
    check_status_code(requests.put(url))

@cmd
def vlan_delete(vlan_id):
    """Delete VLAN number <vlan_id>"""
    url = object_url('vlan', vlan_id)
    check_status_code(requests.delete(url))



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

