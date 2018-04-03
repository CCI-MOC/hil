"""Commands related to headnode are in this module
This is the only module that does not use the client library.
"""

import click
import sys
import os
import urllib
import json
from hil import config
from hil.cli.client_setup import http_client
from hil.client.base import FailedAPICallException


def check_status_code(response):
    """Check the status code of the response.

    If it is a successful status code, print the body of the response to
    stdout. Otherwise, print an error message, and raise a
    FailedAPICallException.
    """
    if response.status_code < 200 or response.status_code >= 300:
        raise FailedAPICallException(response.status_code, response.content)
    else:
        sys.stdout.write(response.content + "\n")


def object_url(*args):
    """Return a url with a prefix of the HIL endpoint, and args as the
    (remaining) segments of the path.

    TODO: This function's name is no longer very accurate.  As soon as it is
    safe, we should change it to something more generic.
    """
    # Prefer an environmental variable for getting the endpoint if available.
    url = os.environ.get('HIL_ENDPOINT')
    if url is None:
        config.setup()
        url = config.cfg.get('client', 'endpoint')

    for arg in args:
        url += '/' + urllib.quote(arg, '')
    return url


def do_put(url, data={}):
    """do a put request and check the response."""
    check_status_code(http_client.request('PUT', url, data=json.dumps(data)))


def do_post(url, data={}):
    """do a post request and check the response."""
    check_status_code(http_client.request('POST', url, data=json.dumps(data)))


def do_get(url, params=None):
    """do a get request and check the response."""
    check_status_code(http_client.request('GET', url, params=params))


def do_delete(url):
    """do a delete request and check the response."""
    check_status_code(http_client.request('DELETE', url))


@click.group()
def headnode():
    """Commands related to headnode"""


@headnode.command(name='create')
@click.argument('headnode')
@click.argument('project')
@click.argument('base-img')
def headnode_create(headnode, project, base_img):
    """Create a <headnode> in a <project> with <base_img>"""
    url = object_url('headnode', headnode)
    do_put(url, data={'project': project,
                      'base_img': base_img})


@headnode.command(name='delete')
@click.argument('headnode')
def headnode_delete(headnode):
    """Delete <headnode>"""
    url = object_url('headnode', headnode)
    do_delete(url)


@headnode.command(name='start')
@click.argument('headnode')
def headnode_start(headnode):
    """Start <headnode>"""
    url = object_url('headnode', headnode, 'start')
    do_post(url)


@headnode.command(name='stop')
@click.argument('headnode')
def headnode_stop(headnode):
    """Stop <headnode>"""
    url = object_url('headnode', headnode, 'stop')
    do_post(url)


@headnode.command(name='list')
@click.argument('project')
def list_project_headnodes(project):
    """List all headnodes attached to a <project>"""
    url = object_url('project', project, 'headnodes')
    do_get(url)


@headnode.command(name='show')
@click.argument('headnode')
def show_headnode(headnode):
    """Display information about a <headnode>"""
    url = object_url('headnode', headnode)
    do_get(url)


@headnode.command(name='list-images')
def list_headnode_images():
    """Display registered headnode images"""
    url = object_url('headnode_images')
    do_get(url)


@headnode.group(name='nic')
def headnode_hnic():
    """Headnode's nics commands"""


@headnode_hnic.command(name='create')
@click.argument('headnode')
@click.argument('nic')
def headnode_create_hnic(headnode, nic):
    """Create a <nic> on the given <headnode>"""
    url = object_url('headnode', headnode, 'hnic', nic)
    do_put(url)


@headnode_hnic.command(name='delete')
@click.argument('headnode')
@click.argument('nic')
def headnode_delete_hnic(headnode, nic):
    """Delete a <nic> on a <headnode>"""
    url = object_url('headnode', headnode, 'hnic', nic)
    do_delete(url)


@headnode.group(name='network')
def headnode_network():
    """Perform headnode network operations"""


@headnode_network.command(name='connect')
@click.argument('headnode')
@click.argument('nic')
@click.argument('network')
def headnode_connect_network(headnode, nic, network):
    """Connect <headnode> to <network> on given <nic>"""
    url = object_url('headnode', headnode, 'hnic', nic, 'connect_network')
    do_post(url, data={'network': network})


@headnode_network.command(name='detach')
@click.argument('headnode')
@click.argument('nic')
@click.argument('network')
def headnode_detach_network(headnode, hnic):
    """Detach <headnode> from the network on given <nic>"""
    url = object_url('headnode', headnode, 'hnic', hnic, 'detach_network')
    do_post(url)
