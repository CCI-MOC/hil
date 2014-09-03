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

import logging
import inspect
import sys
import urllib
import requests

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
        args = ''.join(['<%s>' % name for name in args])
        if varargs:
            varargs = ' <%s...>' % varargs
        else:
            varargs = ''
        return '%s%s%s' % (f.__name__, args, varargs)
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


@cmd
def serve():
    """Start the HaaS API server"""
    if cfg.has_option('devel', 'debug'):
        debug = cfg.getboolean('devel', 'debug')
    else:
        debug = False
    from haas import model, api
    model.init_db()
    api.app.run(debug=debug)

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
def network_create(network, project):
    """Create a <network> belonging to a <project>"""
    url = object_url('network', network)
    check_status_code(requests.put(url, data={'project': project}))

@cmd
def network_delete(network):
    """Delete a <network>"""
    url = object_url('network', network)
    check_status_code(requests.delete(url))

@cmd
def user_delete(username):
    """Delete the user <username>"""
    url = object_url('user', username)
    check_status_code(requests.delete(url))

@cmd
def group_add_user(group, user):
    """Add <user> to <group>"""
    url = object_url('group', group, 'add_user')
    check_status_code(requests.post(url, data={'user': user}))

@cmd
def group_remove_user(group, user):
    """Remove <user> from <group>"""
    url = object_url('group', group, 'remove_user')
    check_status_code(requests.post(url, data={'user': user}))

@cmd
def project_create(project, group):
    """Create <project> belonging to <group>"""
    url = object_url('project', project)
    check_status_code(requests.put(url, data={'group': group}))

@cmd
def project_delete(project):
    """Delete <project>"""
    url = object_url('project', project)
    check_status_code(requests.delete(url))

@cmd
def group_create(group):
    """Create <group>"""
    url = object_url('group', group)
    check_status_code(requests.put(url))

@cmd
def group_delete(group):
    """Delete <group>"""
    url = object_url('group', group)
    check_status_code(requests.delete(url))

@cmd
def project_apply(project):
    """Apply the networking of a <project>"""
    url = object_url('project', project, 'apply')
    check_status_code(requests.post(url))

@cmd
def headnode_create(headnode, project):
    """Create a <headnode> belonging to <project>"""
    url = object_url('headnode', headnode)
    check_status_code(requests.put(url, data={'project': project}))

@cmd
def headnode_delete(headnode):
    """Delete <headnode>"""
    url = object_url('headnode', headnode)
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
def headnode_start(headnode):
    """Start <headnode>"""
    url = object_url('headnode', headnode, 'start')
    check_status_code(requests.post(url))

@cmd
def headnode_stop(headnode):
    """Stop <headnode>"""
    url = object_url('headnode', headnode, 'stop')
    check_status_code(requests.post(url))

@cmd
def node_register(node, ipmi_host, ipmi_user, ipmi_pass):
    """Register a node named <node>, with the given ipmi host/user/password"""
    url = object_url('node', node)
    check_status_code(requests.put(url, data={
        'ipmi_host': ipmi_host,
        'ipmi_user': ipmi_user,
        'ipmi_pass': ipmi_pass}))

@cmd
def node_power_cycle(node):
    """Power cycle <node>"""
    url = object_url('node', node, 'power_cycle')
    check_status_code(requests.post(url))

@cmd
def node_register_nic(node, nic, macaddr):
    """Register existence of a <nic> with the given <macaddr> on the given <node>"""
    url = object_url('node', node, 'nic', nic)
    check_status_code(requests.put(url, data={'macaddr':macaddr}))

@cmd
def node_delete_nic(node, nic):
    """Delete a <nic> on a <node>"""
    url = object_url('node', node, 'nic', nic)
    check_status_code(requests.delete(url))

@cmd
def headnode_create_hnic(headnode, nic, macaddr):
    """Create a <nic> with the given <macaddr> on the given <headnode>"""
    url = object_url('headnode', headnode, 'hnic', nic)
    check_status_code(requests.put(url, data={'macaddr':macaddr}))

@cmd
def headnode_delete_hnic(headnode, nic):
    """Delete a <nic> on a <headnode>"""
    url = object_url('headnode', headnode, 'hnic', nic)
    check_status_code(requests.delete(url))

@cmd
def node_connect_network(node, nic, network):
    """Connect <node> to <network> on given <nic>"""
    url = object_url('node', node, 'nic', nic, 'connect_network')
    check_status_code(requests.post(url, data={'network':network}))

@cmd
def node_detach_network(node, nic):
    """Detach <node> from the network on given <nic>"""
    url = object_url('node', node, 'nic', nic, 'detach_network')
    check_status_code(requests.post(url))

@cmd
def headnode_connect_network(headnode, nic, network):
    """Connect <headnode> to <network> on given <nic>"""
    url = object_url('headnode', headnode, 'hnic', nic, 'connect_network')
    check_status_code(requests.post(url, data={'network':network}))

@cmd
def headnode_detach_network(headnode, nic):
    """Detach <headnode> from the network on given <nic>"""
    url = object_url('headnode', headnode, 'hnic', hnic, 'detach_network')
    check_status_code(requests.post(url))

@cmd
def switch_register(name, driver):
    """Register a switch using driver <driver> under the name <name>"""
    url = object_url('switch', name)
    check_status_code(requests.put(url, data={'driver': driver}))

@cmd
def switch_delete(name):
    """Delete the switch named <name>"""
    url = object_url('switch', name)
    check_status_code(requests.delete(url))

@cmd
def port_register(switch, port):
    """Register a <port> on a <switch>"""
    url = object_url('switch', switch, 'port', port)
    check_status_code(requests.put(url))

@cmd
def port_delete(switch, port):
    """Delete a <port> on a <switch>"""
    url = object_url('switch', switch, 'port', port)
    check_status_code(requests.delete(url))

@cmd
def port_connect_nic(switch, port, node, nic):
    """Connect a <port> on a <switch> to a <nic> on a <node>"""
    url = object_url('switch', switch, 'port', port, 'connect_nic')
    check_status_code(requests.post(url, data={'node': node, 'nic': nic}))

@cmd
def port_detach_nic(switch, port):
    """Detach a <port> on a <switch> from whatever's connected to it"""
    url = object_url('switch', switch, 'port', port, 'detach_nic')
    check_status_code(requests.post(url))

@cmd
def list_free_nodes():
    """List all free nodes"""
    url = object_url('free_nodes')
    check_status_code(requests.get(url))

@cmd
def list_project_nodes(project):
    """List all nodes attached to a <project>"""
    url = object_url('project', project, 'nodes')
    check_status_code(requests.get(url))

@cmd
def show_node(node):
    """Display information about a <node>"""
    url = object_url('node', node)
    check_status_code(requests.get(url))

@cmd
def show_headnode(headnode):
    """Display information about a <headnode>"""
    url = object_url('headnode', headnode)
    check_status_code(requests.get(url))

@cmd
def help(*commands):
    """Display usage of all following <commands>, or of all commands if none are given"""
    if not commands:
        sys.stderr.write('Usage: %s <command> <arguments...> \n' % sys.argv[0])
        sys.stderr.write('Where <command> is one of:\n')
        commands = sorted(command_dict.keys())
    for name in commands:
        # For each command, print out a summary including the name, arguments,
        # and the docstring (as a #comment).
        sys.stderr.write('  %s\n' % usage_dict[name])
        sys.stderr.write('      %s\n' % command_dict[name].__doc__)


def main():
    """Entry point to the CLI.

    There is a script located at ${source_tree}/scripts/haas, which invokes
    this function.
    """
    config.load()

    if cfg.has_option('general', 'log_level'):
        LOG_SET = ["CRITICAL", "DEBUG", "ERROR", "FATAL", "INFO", "WARN",
                   "WARNING"]
        log_level = cfg.get('general', 'log_level').upper()
        if log_level in LOG_SET:
            # Set to mnemonic log level
            logging.basicConfig(level=getattr(logging, log_level))
        else:
            # Set to 'warning', and warn that the config is bad
            logging.basicConfig(level=logging.WARNING)
            logging.getLogger(__name__).warning(
                "Invalid debugging level %s defaulted to WARNING"% log_level)
    else:
        # Default to 'warning'
        logging.basicConfig(level=logging.WARNING)

    if len(sys.argv) < 2 or sys.argv[1] not in command_dict:
        # Display usage for all commands
        help()
    else:
        command_dict[sys.argv[1]](*sys.argv[2:])

