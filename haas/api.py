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

"""This module provides the HaaS service's public API.

TODO: Spec out and document what sanitization is required.
"""
from flask import Flask, request
from functools import wraps
import inspect
import importlib
import json

from haas import model
from haas.config import cfg


class APIError(Exception):
    """An exception indicating an error that should be reported to the user.

    i.e. If such an error occurs in a rest API call, it should be reported as
    part of the HTTP response.
    """


class NotFoundError(APIError):
    """An exception indicating that a given resource does not exist."""


class DuplicateError(APIError):
    """An exception indicating that a given resource already exists."""


class AllocationError(APIError):
    """An exception indicating resource exhaustion."""


class BadArgumentError(APIError):
    """An exception indicating an invalid request on the part of the user."""

class ProjectMismatchError(APIError):
    """An exception indicating that the resources given don't belong to the
    same project.
    """

class BlockedError(APIError):
    """An exception indicating that the requested action cannot happen until
    some other change.  For example, deletion is blocked until the components
    are deleted, and possibly until the dirty flag is cleared as well.
    """

class IllegalStateError(APIError):
    """The request is invalid due to the state of the system.

    The request might otherwise be perfectly valid.
    """


app = Flask(__name__)


def handle_client_errors(f):
    """A decorator which adds some error handling.

    If the function decorated with `handle_client_errors` raises an exception
    of type `APIError`, the error will be reported to the client, whereas
    other exceptions (being indications of a bug in the HaaS) will not be.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            resp = f(*args, **kwargs)
        except APIError as e:
            # Right now we're always returning 400 (Bad Request). This probably
            # isn't actually the right thing to do.
            #
            # Additionally, we're getting deprecation errors about the use of
            # the message attribute. TODO: figure out what the right way to do
            # this is.
            return e.message, 400
        if not resp:
            return ''
        else:
            return resp
    return wrapped


def rest_call(method, path):
    """A decorator which generates a rest mapping to a python api call.

    path - the url-path to map the function to. The format is the same as for
           flask's router (e.g. app.route('/foo/<bar>/baz',...))
    method - the HTTP method for the api call

    Any parameters to the function not designated in the url will be pull from
    the form data.

    For example, given:

        @rest_call('POST', '/some-url/<baz>/<bar>')
        def foo(bar, baz, quux):
            pass

    When a POST request to /some-url/*/* occurs, `foo` will be invoked
    with its bar and baz arguments pulleed from the url, and its quux from
    the form data in the body.

    The original function will returned by the call, not the wrapper. This
    way the test suite doesn't have to deal with the things flask has done
    to it - it can invoke the raw api calls..
    """
    def wrapper(func):
        argnames, _, _, _ = inspect.getargspec(func)

        @app.route(path, methods=[method])
        @wraps(func)
        @handle_client_errors
        def wrapped(*args, **kwargs):
            positional_args = []
            for name in argnames:
                if name in kwargs:
                    positional_args.append(kwargs[name])
                    del kwargs[name]
                else:
                    positional_args.append(request.form[name])
            return func(*positional_args, **kwargs)
        return func
    return wrapper


@rest_call('PUT', '/user/<user>')
def user_create(user, password):
    """Create user with given password

    If the user already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.User, user)
    user = model.User(user, password)
    db.add(user)
    db.commit()


@rest_call('DELETE', '/user/<user>')
def user_delete(user):
    """Delete user `username`

    If the user does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    user = _must_find(db, model.User, user)
    db.delete(user)
    db.commit()

                            # Group Code #
                            ##############


@rest_call('PUT', '/group/<group>')
def group_create(group):
    """Create group.

    If the group already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Group, group)
    group = model.Group(group)
    db.add(group)
    db.commit()


@rest_call('DELETE', '/group/<group>')
def group_delete(group):
    """Delete group.

    If the group does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    group = _must_find(db, model.Group, group)
    db.delete(group)
    db.commit()


@rest_call('POST', '/group/<group>/add_user')
def group_add_user(group, user):
    """Add a user to a group

    If the group or user does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    user = _must_find(db, model.User, user)
    group = _must_find(db, model.Group, group)
    if group in user.groups:
        raise DuplicateError(user.label)
    user.groups.append(group)
    db.commit()


@rest_call('POST', '/group/<group>/remove_user')
def group_remove_user(group, user):
    """Remove a user from a group

    If the group or user does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    user = _must_find(db, model.User, user)
    group = _must_find(db, model.Group, group)
    if group not in user.groups:
        raise NotFoundError(user.label)
    user.groups.remove(group)
    db.commit()

                            # Project Code #
                            ################


@rest_call('PUT', '/project/<project>')
def project_create(project, group):
    """Create project belonging to the given group.

    If the project already exists, a DuplicateError will be raised.

    If the group does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Project, project)
    group = _must_find(db, model.Group, group)
    project = model.Project(group, project)
    db.add(project)
    db.commit()


@rest_call('DELETE', '/project/<project>')
def project_delete(project):
    """Delete project.

    If the project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = _must_find(db, model.Project, project)
    if project.nodes:
        raise BlockedError("Project has nodes still")
    if project.networks:
        raise BlockedError("Project still has networks")
    if project.headnode:
        ### FIXME: If you ever create a headnode, you can't delete it right
        ### now.  This essentially makes deletion of projects impossible.
        raise BlockedError("Project still has a headnode")
    db.delete(project)
    db.commit()


@rest_call('POST', '/project/<project>/apply')
def project_apply(project):
    """Apply networking of project.

    If the project does not exist, a NotFoundError will be raised.

    TODO: there are other possible errors, document them and how they are
    handled.
    """
    driver_name = cfg.get('general', 'active_switch')
    driver = importlib.import_module('haas.drivers.' + driver_name)

    db = model.Session()
    project = _must_find(db, model.Project, project)

    net_map = {}
    for net in project.networks:
        for nic in net.nics:
            net_map[nic.port.label] = net.network_id
    driver.apply_networking(net_map)

    project.dirty = False
    db.commit()

@rest_call('POST', '/project/<project>/connect_node')
def project_connect_node(project, node):
    """Add a node to a project.

    If the node or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = _must_find(db, model.Project, project)
    node = _must_find(db, model.Node, node)
    project.nodes.append(node)
    db.commit()


@rest_call('POST', '/project/<project>/detach_node')
def project_detach_node(project, node):
    """Remove a node from a project.

    If the node or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = _must_find(db, model.Project, project)
    node = _must_find(db, model.Node, node)
    if node not in project.nodes:
        raise NotFoundError("Node not in project")
    for nic in node.nics:
        if nic.network is not None:
            raise BlockedError("Node attached to a network")
    if project.dirty:
        raise BlockedError("Project dirty")
    project.nodes.remove(node)
    db.commit()


                            # Node Code #
                            #############


@rest_call('PUT', '/node/<node>')
def node_register(node):
    """Create node.

    If the node already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Node, node)
    node = model.Node(node)
    db.add(node)
    db.commit()


@rest_call('DELETE', '/node/<node>')
def node_delete(node):
    """Delete node.

    If the node does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    node = _must_find(db, model.Node, node)
    db.delete(node)
    db.commit()


@rest_call('PUT', '/node/<node>/nic/<nic>')
def node_register_nic(node, nic, macaddr):
    """Register exitence of nic attached to given node

    If the node does not exist, a NotFoundError will be raised.

    If there is already an nic with that name, a DuplicateError will be raised.
    """
    db = model.Session()
    node = _must_find(db, model.Node, node)
    _assert_absent_n(db, node, model.Nic, nic)
    nic = model.Nic(node, nic, macaddr)
    db.add(nic)
    db.commit()


@rest_call('DELETE', '/node/<node>/nic/<nic>')
def node_delete_nic(node, nic):
    """Delete nic with given name.

    If the nic does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    nic = _must_find_n(db, _must_find(db, model.Node, node), model.Nic, nic)
    db.delete(nic)
    db.commit()


@rest_call('POST', '/node/<node>/nic/<nic>/connect_network')
def node_connect_network(node, nic, network):
    """Connect a physical NIC to a network"""
    db = model.Session()

    node = _must_find(db, model.Node, node)
    nic = _must_find_n(db, node, model.Nic, nic)
    network = _must_find(db, model.Network, network)

    if not node.project:
        raise ProjectMismatchError("Node not in project")

    if node.project.label is not network.project.label:
        raise ProjectMismatchError("Node and network in different projects")

    project = node.project

    if nic.network:
        # The nic is already part of a network; report an error to the user.
        raise DuplicateError('nic %s on node %s is already part of a network' %
                (nic.label, node.label))

    nic.network = network
    project.dirty = True
    db.commit()


@rest_call('POST', '/node/<node>/nic/<nic>/detach_network')
def node_detach_network(node, nic):
    """Detach a physical nic from its network (if any).

    If the nic is not already a member of a network, this function does
    nothing.
    """
    db = model.Session()
    node = _must_find(db, model.Node, node)
    nic = _must_find_n(db, node, model.Nic, nic)

    if not node.project:
        raise ProjectMismatchError("Node not in project")

    project = nic.owner.project

    if nic.network is None:
        raise NotFoundError('nic %s on node %s is not attached' % (nic.label, node.label))

    nic.network = None
    project.dirty = True
    db.commit()

                            # Head Node Code #
                            ##################


@rest_call('PUT', '/headnode/<headnode>')
def headnode_create(headnode, project):
    """Create headnode.

    If a node with the same name already exists, a DuplicateError will be
    raised.

    If the project already has a headnode, a DuplicateError will be raised.

    If the project does not exist, a NotFoundError will be raised.

    """
    db = model.Session()

    _assert_absent(db, model.Headnode, headnode)
    project = _must_find(db, model.Project, project)

    if project.headnode is not None:
        raise DuplicateError('project %s already has a headnode' %
                             (project.label))

    headnode = model.Headnode(project, headnode)

    db.add(headnode)
    db.commit()


@rest_call('DELETE', '/headnode/<headnode>')
def headnode_delete(headnode):
    """Delete headnode

    If the node does not exist, a NotFoundError will be raised.
    """
    ### XXX This should never succeed currently.
    db = model.Session()
    headnode = _must_find(db, model.Headnode, headnode)
    db.delete(headnode)
    db.commit()


@rest_call('POST', '/headnode/<headnode>/start')
def headnode_start(headnode):
    """Start the headnode.

    This actually boots up the headnode virtual machine. The VM is created
    within libvirt if needed. Once the VM has been started once, it is
    "frozen," and all other headnode-related api calls will fail (by raising
    an IllegalStateException), with the exception of headnode_stop.
    """
    db = model.Session()
    headnode = _must_find(db, model.Headnode, headnode)
    if headnode.dirty:
        headnode.create()
    headnode.start()
    db.commit()


@rest_call('POST', '/headnode/<headnode>/stop')
def headnode_stop(headnode):
    """Stop the headnode.

    This powers off the headnode. This is a hard poweroff; the VM is not given
    the opportunity to shut down cleanly. This does *not* unfreeze the VM;
    headnode_start will be the only valid API call after the VM is powered off.
    """
    db = model.Session()
    headnode = _must_find(db, model.Headnode, headnode)
    headnode.stop()


@rest_call('PUT', '/headnode/<headnode>/hnic/<hnic>')
def headnode_create_hnic(headnode, hnic, macaddr):
    """Create hnic attached to given headnode

    If the node does not exist, a NotFoundError will be raised.

    If there is already an hnic with that name, a DuplicateError will
    be raised.
    """
    db = model.Session()
    headnode = _must_find(db, model.Headnode, headnode)
    _assert_absent_n(db, headnode, model.Hnic, hnic)

    if not headnode.dirty:
        raise IllegalStateError

    hnic = model.Hnic(headnode, hnic, macaddr)
    db.add(hnic)
    db.commit()


@rest_call('DELETE', '/headnode/<headnode>/hnic/<hnic>')
def headnode_delete_hnic(headnode, hnic):
    """Delete hnic with given name.

    If the hnic does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    headnode = _must_find(db, model.Headnode, headnode)
    hnic = _must_find_n(db, headnode, model.Hnic, hnic)

    if not headnode.dirty:
        raise IllegalStateError
    if not hnic:
        raise NotFoundError("Hnic: " + hnic.label)

    db.delete(hnic)
    db.commit()


@rest_call('POST', '/headnode/<headnode>/hnic/<hnic>/connect_network')
def headnode_connect_network(headnode, hnic, network):
    """Connect a headnode's NIC to a network"""
    db = model.Session()

    headnode = _must_find(db, model.Headnode, headnode)
    hnic = _must_find_n(db, headnode, model.Hnic, hnic)
    network = _must_find(db, model.Network, network)

    if not headnode.dirty:
        raise IllegalStateError

    if headnode.project.label is not network.project.label:
        raise ProjectMismatchError("Headnode and network in different projects")

    if hnic.network:
        # The nic is already part of a network; report an error to the user.
        raise DuplicateError('hnic %s on headnode %s is already part of a network' %
                (hnic.label, headnode.label))
    hnic.network = network
    headnode.project.dirty = True
    db.commit()


@rest_call('POST', '/headnode/<headnode>/hnic/<hnic>/detach_network')
def headnode_detach_network(headnode, hnic):
    """Detach a heanode's nic from its network (if any).

    If the nic is not already a member of a network, this function does
    nothing.
    """
    db = model.Session()

    headnode = _must_find(db, model.Headnode, headnode)
    hnic = _must_find_n(db, headnode, model.Hnic, hnic)

    if not headnode.dirty:
        raise IllegalStateError

    if hnic.network is None:
        raise NotFoundError('hnic %s on headnode %s not attached'
                            % (hnic.label, headnode.label))

    hnic.network = None
    headnode.project.dirty = True
    db.commit()

                            # Network Code #
                            ################


@rest_call('PUT', '/network/<network>')
def network_create(network, project):
    """Create network 'network'.

    If the network already exists, a DuplicateError will be raised.
    If the network cannot be allocated (due to resource exhaustion), an
    AllocationError will be raised.
    """
    projectname = project

    db = model.Session()
    _assert_absent(db, model.Network, network)
    project = _must_find(db, model.Project, project)

    driver_name = cfg.get('general', 'active_switch')
    driver = importlib.import_module('haas.drivers.' + driver_name)
    network_id = driver.get_new_network_id(db)
    if network_id is None:
        raise AllocationError('No more networks')

    network = model.Network(project, network_id, network)
    db.add(network)
    db.commit()


@rest_call('DELETE', '/network/<network>')
def network_delete(network):
    """Delete network 'network'

    If the network does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    network = _must_find(db, model.Network, network)

    if network.nics:
        raise BlockedError("Network still connected to nodes")
    if network.hnics:
        raise BlockedError("Network still connected to headnodes")
    if network.project.dirty:
        raise BlockedError("Project dirty")

    driver_name = cfg.get('general', 'active_switch')
    driver = importlib.import_module('haas.drivers.' + driver_name)
    driver.free_network_id(db, network.network_id)

    db.delete(network)
    db.commit()


                            # Switch code #
                            ###############

@rest_call('PUT', '/switch/<switch>')
def switch_register(switch, driver):
    """Register the switch 'switch'.

    If the switch already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Switch, switch)
    switch = model.Switch(switch, driver)
    db.add(switch)
    db.commit()


@rest_call('DELETE', '/switch/<switch>')
def switch_delete(switch):
    db = model.Session()
    switch = _must_find(db, model.Switch, switch)
    db.delete(switch)
    db.commit()


@rest_call('PUT', '/switch/<switch>/port/<port>')
def port_register(switch, port):
    """Register a port with name "port" on switch "switch".

    If the port already exists, a DuplicateError will be raised.

    If the switch does not exist, a NotFoundError will be raised.
    """
    db = model.Session()

    switch = _must_find(db, model.Switch, switch)
    _assert_absent_n(db, switch, model.Port, port)

    port = model.Port(switch, port)
    db.add(port)
    db.commit()


@rest_call('DELETE', '/switch/<switch>/port/<port>')
def port_delete(switch, port):
    """Delete a port with name "port" on switch "switch".

    If the port does not exist, or if the switch does not exist, a
    NotFoundError will be raised.
    """
    db = model.Session()

    port = _must_find_n(db, _must_find(db, model.Switch, switch), model.Port, port)

    db.delete(port)
    db.commit()


@rest_call('POST', '/switch/<switch>/port/<port>/connect_nic')
def port_connect_nic(switch, port, node, nic):
    """Connect a port on a switch to a nic on a node

    If any of the four arguments does not exist, a NotFoundError will be
    raised.

    If the port or the nic are already connected to something, a
    DuplicateError will be raised.
    """
    db = model.Session()

    port = _must_find_n(db, _must_find(db, model.Switch, switch), model.Port, port)
    nic = _must_find_n(db, _must_find(db, model.Node, node), model.Nic, nic)

    if nic.port is not None:
        raise DuplicateError(nic.label)

    if port.nic is not None:
        raise DuplicateError(port.label)

    nic.port = port
    db.commit()


@rest_call('POST', '/switch/<switch>/port/<port>/detach_nic')
def port_detach_nic(switch, port):
    """Detach attached nic from a port

    If the port or switch are not found, a NotFoundError will be raised.

    If the port is not connected to anything, a NotFoundError will be raised.
    """
    db = model.Session()

    port = _must_find_n(db, _must_find(db, model.Switch, switch), model.Port, port)

    if port.nic is None:
        raise NotFoundError(port.label + " not attached")

    port.nic = None
    db.commit()


@rest_call('GET', '/free_nodes')
def list_free_nodes():
    db = model.Session()
    nodes = db.query(model.Node).filter_by(project_id=None).all()
    nodes = map(lambda n: n.label, nodes)
    return json.dumps(nodes)


@rest_call('GET', '/project/<project>/nodes')
def list_project_nodes(project):
    db = model.Session()
    project = _must_find(db, model.Project, project)
    nodes = project.nodes
    nodes = map(lambda n: n.label, nodes)
    return json.dumps(nodes)


@rest_call('GET', '/node/<nodename>')
def show_node(nodename):
    db = model.Session()
    node = _must_find(db, model.Node, nodename)
    return json.dumps({
        'name': node.label,
        'free': node.project_id is None,
        'nics': map(lambda n: n.label, node.nics),
    })


@rest_call('GET', '/headnode/<nodename>')
def show_headnode(nodename):
    db = model.Session()
    headnode = _must_find(db, model.Headnode, nodename)
    return json.dumps({
        'name': headnode.label,
        'project': headnode.project.label,
        'hnics': map(lambda n: n.label, headnode.hnics),
    })


    # Helper functions #
    ####################


def _assert_absent(session, cls, name):
    """Raises a DuplicateError if the given object is already in the database.

    This is useful for most of the *_create functions.

    Arguments:

    session - a sqlaclhemy session to use.
    cls - the class of the object to query.
    name - the name of the object in question.
    """
    obj = session.query(cls).filter_by(label=name).first()
    if obj:
        raise DuplicateError(cls.__name__ + ': ' + name)


def _must_find(session, cls, name):
    """Raises a NotFoundError if the given object doesn't exist in the datbase.
    Otherwise returns the object

    This is useful for most of the *_delete functions.

    Arguments:

    session - a sqlaclhemy session to use.
    cls - the class of the object to query.
    name - the name of the object in question.
    """
    obj = session.query(cls).filter_by(label=name).first()
    if not obj:
        raise NotFoundError(cls.__name__ + ': ' + name)
    return obj

def _assert_absent_n(session, obj_outer, cls_inner, name_inner):
    """Raises DuplicateError if a "namespaced" object, such as a node's nic, exists.

    Otherwise returns succesfully.

    Arguments:

    session - a SQLAlchemy session to use.
    obj_outer - the "owner" object
    cls_inner - the "owned" class
    name_inner - the name of the "owned" object
    """
    obj_inner = session.query(cls_inner) \
        .filter_by(owner = obj_outer) \
        .filter_by(label = name_inner).first()
    if obj_inner is not None:
        raise DuplicateError(cls_inner.__name__ + " " + obj_outer.label + " " + name_inner)

def _must_find_n(session, obj_outer, cls_inner, name_inner):
    """Searches the database for a "namespaced" object, such as a nic on a node.

    Raises NotFoundError if there is none.  Otherwise returns the object.

    Arguments:

    session - a SQLAlchemy session to use.
    obj_outer - the "owner" object
    cls_inner - the "owned" class
    name_inner - the name of the "owned" object
    """
    obj_inner = session.query(cls_inner) \
        .filter_by(owner = obj_outer) \
        .filter_by(label = name_inner).first()
    if obj_inner is None:
        raise NotFoundError(cls_inner.__name__ + " " + obj_outer.label + " " + name_inner)
    return obj_inner
