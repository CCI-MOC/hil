# Copyright 2013-2014 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

"""This module implements the HaaS command line tool."""
from haas import config
from haas.config import cfg

import inspect
import sys
import urllib
import requests
import json

from functools import wraps

command_dict = {}
usage_dict = {}

def cmd(f):
    """A decorator for CLI commands.

    This decorator firstly adds the function to a dictionary of valid CLI
    commands, secondly adds exception handling for when the user passes the
    wrong number of arguments, and thirdly generates a 'usage' description and
    puts it in the usage dictionary.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except TypeError:
            # TODO TypeError is probably too broad here.
            sys.stderr.write('Wrong number of arguements.  Usage:\n')
            help(f.__name__)
    command_dict[f.__name__] = wrapped
    def get_usage(f):
        args, varargs, _, _ = inspect.getargspec(f)
        showee = [f.__name__] + ['<%s>' % name for name in args]
        args = ' '.join(['<%s>' % name for name in args])
        if varargs:
            showee += ['<%s...>' % varargs]
        return ' '.join(showee)
    usage_dict[f.__name__] = get_usage(f)
    return wrapped


def check_status_code(response):
    if response.status_code < 200 or response.status_code >= 300:
        sys.stderr.write('Unexpected status code: %d\n' % response.status_code)
        sys.stderr.write('Response text:\n')
        sys.stderr.write(response.text + "\n")
    else:
        sys.stdout.write(response.text + "\n")

# TODO: This function's name is no longer very accurate.  As soon as it is
# safe, we should change it to something more generic.
def object_url(*args):
    url = cfg.get('client', 'endpoint')
    for arg in args:
        url += '/' + urllib.quote(arg,'')
    return url

def do_put(url, data={}):
    return check_status_code(requests.put(url, data=json.dumps(data)))

def do_post(url, data={}):
    return check_status_code(requests.post(url, data=json.dumps(data)))

def do_get(url):
    return check_status_code(requests.get(url))

def do_delete(url):
    return check_status_code(requests.delete(url))

@cmd
def serve():
    """Start the HaaS API server"""
    if cfg.has_option('devel', 'debug'):
        debug = cfg.getboolean('devel', 'debug')
    else:
        debug = False
    # We need to import api here so that the functions within it get registered
    # (via `rest_call`), though we don't use it directly:
    from haas import model, api, rest
    model.init_db()
    # Stop all orphan console logging processes on startup
    db = model.Session()
    nodes = db.query(model.Node).all()
    for node in nodes:
        node.stop_console()
        node.delete_console()
    # Start server
    rest.serve(debug=debug)


@cmd
def serve_networks():
    """Start the HaaS networking server"""
    from haas import model, deferred
    from time import sleep
    model.init_db()
    while True:
        # Empty the journal until it's empty; then delay so we don't tight
        # loop.
        while deferred.apply_networking():
            pass
        sleep(2)

@cmd
def init_db():
    """Initialize the database"""
    from haas import model
    model.init_db(create=True)

@cmd
def user_create(username, password):
    """Create a user <username> with password <password>."""
    url = object_url('user', username)
    do_put(url, data={'password': password})

@cmd
def network_create(network, creator, access, net_id):
    """Create a link-layer <network>.  See docs/networks.md for details"""
    url = object_url('network', network)
    do_put(url, data={'creator': creator,
                      'access': access,
                      'net_id': net_id})

@cmd
def network_create_simple(network, project):
    """Create <network> owned by project.  Specific case of network_create"""
    url = object_url('network', network)
    do_put(url, data={'creator': project,
                      'access': project,
                      'net_id': ""})

@cmd
def network_delete(network):
    """Delete a <network>"""
    url = object_url('network', network)
    do_delete(url)

@cmd
def user_delete(username):
    """Delete the user <username>"""
    url = object_url('user', username)
    do_delete(url)

@cmd
def project_add_user(project, user):
    """Add <user> to <project>"""
    url = object_url('project', project, 'add_user')
    do_post(url, data={'user': user})

@cmd
def project_remove_user(project, user):
    """Remove <user> from <project>"""
    url = object_url('project', project, 'remove_user')
    do_post(url, data={'user': user})

@cmd
def project_create(project):
    """Create a <project>"""
    url = object_url('project', project)
    do_put(url)

@cmd
def project_delete(project):
    """Delete <project>"""
    url = object_url('project', project)
    do_delete(url)

@cmd
def headnode_create(headnode, project, base_img):
    """Create a <headnode> in a <project> with <base_img>"""
    url = object_url('headnode', headnode)
    do_put(url, data={'project': project,
                      'base_img': base_img})

@cmd
def headnode_delete(headnode):
    """Delete <headnode>"""
    url = object_url('headnode', headnode)
    do_delete(url)

@cmd
def project_connect_node(project, node):
    """Connect <node> to <project>"""
    url = object_url('project', project, 'connect_node')
    do_post(url, data={'node': node})

@cmd
def project_detach_node(project, node):
    """Detach <node> from <project>"""
    url = object_url('project', project, 'detach_node')
    do_post(url, data={'node': node})

@cmd
def headnode_start(headnode):
    """Start <headnode>"""
    url = object_url('headnode', headnode, 'start')
    do_post(url)

@cmd
def headnode_stop(headnode):
    """Stop <headnode>"""
    url = object_url('headnode', headnode, 'stop')
    do_post(url)

@cmd
def node_register(node, ipmi_host, ipmi_user, ipmi_pass):
    """Register a node named <node>, with the given ipmi host/user/password"""
    url = object_url('node', node)
    do_put(url, data={'ipmi_host': ipmi_host,
                      'ipmi_user': ipmi_user,
                      'ipmi_pass': ipmi_pass})

@cmd
def node_delete(node):
    """Delete <node>"""
    url = object_url('node', node)
    do_delete(url)

@cmd
def node_power_cycle(node):
    """Power cycle <node>"""
    url = object_url('node', node, 'power_cycle')
    do_post(url)

@cmd
def node_register_nic(node, nic, macaddr):
    """Register existence of a <nic> with the given <macaddr> on the given <node>"""
    url = object_url('node', node, 'nic', nic)
    do_put(url, data={'macaddr':macaddr})

@cmd
def node_delete_nic(node, nic):
    """Delete a <nic> on a <node>"""
    url = object_url('node', node, 'nic', nic)
    do_delete(url)

@cmd
def headnode_create_hnic(headnode, nic):
    """Create a <nic> on the given <headnode>"""
    url = object_url('headnode', headnode, 'hnic', nic)
    do_put(url)

@cmd
def headnode_delete_hnic(headnode, nic):
    """Delete a <nic> on a <headnode>"""
    url = object_url('headnode', headnode, 'hnic', nic)
    do_delete(url)

@cmd
def node_connect_network(node, nic, network):
    """Connect <node> to <network> on given <nic>"""
    url = object_url('node', node, 'nic', nic, 'connect_network')
    do_post(url, data={'network':network})

@cmd
def node_detach_network(node, nic):
    """Detach <node> from the network on given <nic>"""
    url = object_url('node', node, 'nic', nic, 'detach_network')
    do_post(url)

@cmd
def headnode_connect_network(headnode, nic, network):
    """Connect <headnode> to <network> on given <nic>"""
    url = object_url('headnode', headnode, 'hnic', nic, 'connect_network')
    do_post(url, data={'network':network})

@cmd
def headnode_detach_network(headnode, nic):
    """Detach <headnode> from the network on given <nic>"""
    url = object_url('headnode', headnode, 'hnic', hnic, 'detach_network')
    do_post(url)

@cmd
def port_register(port):
    """Register a <port> on a switch"""
    url = object_url('port', port)
    do_put(url)

@cmd
def port_delete(port):
    """Delete a <port> on a switch"""
    url = object_url('port', port)
    do_delete(url)

@cmd
def port_connect_nic(port, node, nic):
    """Connect a <port> on a switch to a <nic> on a <node>"""
    url = object_url('port', port, 'connect_nic')
    do_post(url, data={'node': node, 'nic': nic})

@cmd
def port_detach_nic(port):
    """Detach a <port> on a switch from whatever's connected to it"""
    url = object_url('port', port, 'detach_nic')
    do_post(url)

@cmd
def list_free_nodes():
    """List all free nodes"""
    url = object_url('free_nodes')
    do_get(url)

@cmd
def list_project_nodes(project):
    """List all nodes attached to a <project>"""
    url = object_url('project', project, 'nodes')
    do_get(url)

@cmd
def list_project_networks(project):
    """List all networks attached to a <project>"""
    url = object_url('project', project, 'networks')
    do_get(url)

@cmd
def show_node(node):
    """Display information about a <node>"""
    url = object_url('node', node)
    do_get(url)

@cmd
def show_headnode(headnode):
    """Display information about a <headnode>"""
    url = object_url('headnode', headnode)
    do_get(url)

@cmd
def list_headnode_images():
    """Display registered headnode images"""
    url = object_url('headnode_images')
    do_get(url)

@cmd
def show_console(node):
    """Display console log for <node>"""
    url = object_url('node', node, 'console')
    do_get(url)

@cmd
def start_console(node):
    """Start logging console output from <node>"""
    url = object_url('node', node, 'console')
    do_put(url)

@cmd
def stop_console(node):
    """Stop logging console output from <node> and delete the log"""
    url = object_url('node', node, 'console')
    do_delete(url)

@cmd
def help(*commands):
    """Display usage of all following <commands>, or of all commands if none are given"""
    if not commands:
        sys.stdout.write('Usage: %s <command> <arguments...> \n' % sys.argv[0])
        sys.stdout.write('Where <command> is one of:\n')
        commands = sorted(command_dict.keys())
    for name in commands:
        # For each command, print out a summary including the name, arguments,
        # and the docstring (as a #comment).
        sys.stdout.write('  %s\n' % usage_dict[name])
        sys.stdout.write('      %s\n' % command_dict[name].__doc__)


def main():
    """Entry point to the CLI.

    There is a script located at ${source_tree}/scripts/haas, which invokes
    this function.
    """
    config.load()
    config.configure_logging()

    if len(sys.argv) < 2 or sys.argv[1] not in command_dict:
        # Display usage for all commands
        help()
    else:
        command_dict[sys.argv[1]](*sys.argv[2:])

