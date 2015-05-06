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
import importlib
import json

from haas import model
from haas.config import cfg
from haas.rest import rest_call
from haas.errors import *


@rest_call('PUT', '/user/<user>')
def user_create(user, password):
    """Create user with given password.

    If the user already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.User, user)
    user = model.User(user, password)
    db.add(user)
    db.commit()


@rest_call('DELETE', '/user/<user>')
def user_delete(user):
    """Delete user.

    If the user does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    user = _must_find(db, model.User, user)
    db.delete(user)
    db.commit()


                            # Project Code #
                            ################


@rest_call('PUT', '/project/<project>')
def project_create(project):
    """Create a project.

    If the project already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Project, project)
    project = model.Project(project)
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
    if project.networks_created:
        raise BlockedError("Project still has networks")
    if project.networks_access:
        ### FIXME: This is not the user's fault, and they cannot fix it.  The
        ### only reason we need to error here is that, with how network access
        ### is done, the following bad thing happens.  If there's a network
        ### that only the project can access, its "access" field will be the
        ### project.  When you then delete that project, "access" will be set
        ### to None instead.  Counter-intuitively, this then makes that
        ### network accessible to ALL PROJECTS!  Once we use real ACLs, this
        ### will not be an issue---instead, the network will be accessible by
        ### NO projects.
        raise BlockedError("Project can still access networks")
    if project.headnodes:
        raise BlockedError("Project still has a headnode")
    db.delete(project)
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
        if nic.current_action is not None:
            raise BlockedError("Node has a networking operation active on it.")
    node.stop_console()
    node.delete_console()
    project.nodes.remove(node)
    db.commit()


@rest_call('POST', '/project/<project>/add_user')
def project_add_user(project, user):
    """Add a user to a project.

    If the project or user does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    user = _must_find(db, model.User, user)
    project = _must_find(db, model.Project, project)
    if project in user.projects:
        raise DuplicateError('User %s is already in project %s'%
                             (user.label, project.label))
    user.projects.append(project)
    db.commit()


@rest_call('POST', '/project/<project>/remove_user')
def project_remove_user(project, user):
    """Remove a user from a project.

    If the project or user does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    user = _must_find(db, model.User, user)
    project = _must_find(db, model.Project, project)
    if project not in user.projects:
        raise NotFoundError("User %s is not in project %s"%
                            (user.label, project.label))
    user.projects.remove(project)
    db.commit()


                            # Node Code #
                            #############


@rest_call('PUT', '/node/<node>')
def node_register(node, ipmi_host, ipmi_user, ipmi_pass):
    """Create node.

    If the node already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Node, node)
    node = model.Node(node, ipmi_host, ipmi_user, ipmi_pass)
    db.add(node)
    db.commit()


@rest_call('POST', '/node/<node>/power_cycle')
def node_power_cycle(node):
    db = model.Session()
    node = _must_find(db, model.Node, node)
    node.power_cycle()


@rest_call('DELETE', '/node/<node>')
def node_delete(node):
    """Delete node.

    If the node does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    node = _must_find(db, model.Node, node)
    node.stop_console()
    node.delete_console()
    db.delete(node)
    db.commit()


@rest_call('PUT', '/node/<node>/nic/<nic>')
def node_register_nic(node, nic, macaddr):
    """Register exitence of nic attached to given node.

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
    """Connect a physical NIC to a network.

    Raises ProjectMismatchError if the node is not in a project, or if the
    project does not have access rights to the given network.
    """
    db = model.Session()

    node = _must_find(db, model.Node, node)
    nic = _must_find_n(db, node, model.Nic, nic)
    network = _must_find(db, model.Network, network)

    if not node.project:
        raise ProjectMismatchError("Node not in project")

    project = node.project

    if nic.current_action:
        raise BlockedError("A networking operation is already active on the nic.")

    if (network.access is not None) and (network.access is not project):
        raise ProjectMismatchError("Project does not have access to given network.")

    db.add(model.NetworkingAction(nic, network))
    db.commit()

@rest_call('POST', '/node/<node>/nic/<nic>/detach_network')
def node_detach_network(node, nic):
    """Detach a physical nic from any network it's on.

    Raises ProjectMismatchError if the node is not in a project.
    """
    db = model.Session()
    node = _must_find(db, model.Node, node)
    nic = _must_find_n(db, node, model.Nic, nic)

    if not node.project:
        raise ProjectMismatchError("Node not in project")

    project = nic.owner.project

    if nic.current_action:
        raise BlockedError("A networking operation is already active on the nic.")

    db.add(model.NetworkingAction(nic, None))
    db.commit()


                            # Head Node Code #
                            ##################


@rest_call('PUT', '/headnode/<headnode>')
def headnode_create(headnode, project, base_img):
    """Create headnode.

    If a node with the same name already exists, a DuplicateError will be
    raised.

    If the project already has a headnode, a DuplicateError will be raised.

    If the project does not exist, a NotFoundError will be raised.

    """

    valid_imgs = cfg.get('headnode', 'base_imgs')
    valid_imgs = [img.strip() for img in valid_imgs.split(',')]

    if base_img not in valid_imgs:
        raise BadArgumentError('Provided image is not a valid image.')
    db = model.Session()

    _assert_absent(db, model.Headnode, headnode)
    project = _must_find(db, model.Project, project)

    headnode = model.Headnode(project, headnode, base_img)

    db.add(headnode)
    db.commit()


@rest_call('DELETE', '/headnode/<headnode>')
def headnode_delete(headnode):
    """Delete headnode.

    If the node does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    headnode = _must_find(db, model.Headnode, headnode)
    if not headnode.dirty:
        headnode.delete()
    for hnic in headnode.hnics:
        db.delete(hnic)
    db.delete(headnode)
    db.commit()


@rest_call('POST', '/headnode/<headnode>/start')
def headnode_start(headnode):
    """Start the headnode.

    This actually boots up the headnode virtual machine. The VM is created
    within libvirt if needed. Once the VM has been started once, it is
    "frozen," and all other headnode-related api calls will fail (by raising
    an IllegalStateError), with the exception of headnode_stop.
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
def headnode_create_hnic(headnode, hnic):
    """Create hnic attached to given headnode.

    If the node does not exist, a NotFoundError will be raised.

    If there is already an hnic with that name, a DuplicateError will
    be raised.
    """
    db = model.Session()
    headnode = _must_find(db, model.Headnode, headnode)
    _assert_absent_n(db, headnode, model.Hnic, hnic)

    if not headnode.dirty:
        raise IllegalStateError

    hnic = model.Hnic(headnode, hnic)
    db.add(hnic)
    db.commit()


@rest_call('DELETE', '/headnode/<headnode>/hnic/<hnic>')
def headnode_delete_hnic(headnode, hnic):
    """Delete hnic on a given headnode.

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
    """Connect a headnode's hnic to a network.

    Raises IllegalStateError if the headnode has already been started.

    Raises ProjectMismatchError if the project does not have access rights to
    the given network.

    Raises BadArgumentError if the network is a non-allocated network. This
    is currently unsupported due to an implementation limitation, but will be
    supported in a future release. See issue #333.
    """
    db = model.Session()

    headnode = _must_find(db, model.Headnode, headnode)
    hnic = _must_find_n(db, headnode, model.Hnic, hnic)
    network = _must_find(db, model.Network, network)

    if not network.allocated:
        raise BadArgumentError("Headnodes may only be connected to networks "
                               "allocated by the project.")

    if not headnode.dirty:
        raise IllegalStateError

    project = headnode.project

    if (network.access is not None) and (network.access is not project):
        raise ProjectMismatchError("Project does not have access to given network.")

    hnic.network = network
    db.commit()


@rest_call('POST', '/headnode/<headnode>/hnic/<hnic>/detach_network')
def headnode_detach_network(headnode, hnic):
    """Detach a heanode's nic from any network it's on.

    Raises IllegalStateError if the headnode has already been started.
    """
    db = model.Session()

    headnode = _must_find(db, model.Headnode, headnode)
    hnic = _must_find_n(db, headnode, model.Hnic, hnic)

    if not headnode.dirty:
        raise IllegalStateError

    hnic.network = None
    db.commit()

                            # Network Code #
                            ################


@rest_call('PUT', '/network/<network>')
def network_create(network, creator, access, net_id):
    """Create a network.

    If the network with that name already exists, a DuplicateError will be
    raised.

    If the combination of creator, access, and net_id is illegal, a
    BadArgumentError will be raised.

    If network ID allocation was requested, and the network cannot be
    allocated (due to resource exhaustion), an AllocationError will be raised.

    Pass 'admin' as creator for an administrator-owned network.  Pass '' as
    access for a publicly accessible network.  Pass '' as net_id if you wish
    to use the HaaS's network-id allocation pool.

    Details of the various combinations of network attributes are in
    docs/networks.md
    """
    db = model.Session()
    _assert_absent(db, model.Network, network)

    # Check legality of arguments, and find correct 'access' and 'creator'
    if creator != "admin":
        # Project-owned network
        if access != creator:
            raise BadArgumentError("Project-created networks must be accessed only by that project.")
        if net_id != "":
            raise BadArgumentError("Project-created networks must use network ID allocation")
        creator = _must_find(db, model.Project, creator)
        access = _must_find(db, model.Project, access)
    else:
        # Administrator-owned network
        creator = None
        if access == "":
            access = None
        else:
            access = _must_find(db, model.Project, access)

    # Allocate net_id, if requested
    if net_id == "":
        driver_name = cfg.get('general', 'driver')
        driver = importlib.import_module('haas.drivers.' + driver_name)
        net_id = driver.get_new_network_id(db)
        if net_id is None:
            raise AllocationError('No more networks')
        allocated = True
    else:
        allocated = False

    network = model.Network(creator, access, allocated, net_id, network)
    db.add(network)
    db.commit()


@rest_call('DELETE', '/network/<network>')
def network_delete(network):
    """Delete network.

    If the network does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    network = _must_find(db, model.Network, network)

    if network.nics:
        raise BlockedError("Network still connected to nodes")
    if network.hnics:
        raise BlockedError("Network still connected to headnodes")
    if network.scheduled_nics:
        raise BlockedError("Network scheduled to become connected to nodes.")
    if network.allocated:
        driver_name = cfg.get('general', 'driver')
        driver = importlib.import_module('haas.drivers.' + driver_name)
        driver.free_network_id(db, network.network_id)

    db.delete(network)
    db.commit()


                            # Port code #
                            #############


@rest_call('PUT', '/port/<path:port>')
def port_register(port):
    """Register a port on a switch.

    If the port already exists, a DuplicateError will be raised.
    """
    db = model.Session()

    _assert_absent(db, model.Port, port)
    port = model.Port(port)

    db.add(port)
    db.commit()


@rest_call('DELETE', '/port/<path:port>')
def port_delete(port):
    """Delete a port on a switch.

    If the port does not exist, a NotFoundError will be raised.
    """
    db = model.Session()

    port = _must_find(db, model.Port, port)

    db.delete(port)
    db.commit()


@rest_call('POST', '/port/<path:port>/connect_nic')
def port_connect_nic(port, node, nic):
    """Connect a port on a switch to a nic on a node.

    If any of the three arguments does not exist, a NotFoundError will be
    raised.

    If the port or the nic is already connected to something, a DuplicateError will be
    raised.
    """
    db = model.Session()

    port = _must_find(db, model.Port, port)
    nic = _must_find_n(db, _must_find(db, model.Node, node), model.Nic, nic)

    if nic.port is not None:
        raise DuplicateError(nic.label)

    if port.nic is not None:
        raise DuplicateError(port.label)

    nic.port = port
    db.commit()


@rest_call('POST', '/port/<path:port>/detach_nic')
def port_detach_nic(port):
    """Detach a port from the nic it's attached to

    If the port does not exist, a NotFoundError will be raised.

    If the port is not connected to anything, a NotFoundError will be raised.
    """
    db = model.Session()

    port = _must_find(db, model.Port, port)

    if port.nic is None:
        raise NotFoundError(port.label + " not attached")

    port.nic = None
    db.commit()


@rest_call('GET', '/free_nodes')
def list_free_nodes():
    """List all nodes not in any project.

    Returns a JSON array of strings representing a list of nodes.

    Example:  '["node1", "node2", "node3"]'
    """
    db = model.Session()
    nodes = db.query(model.Node).filter_by(project_id=None).all()
    nodes = [n.label for n in nodes]
    return json.dumps(nodes)


@rest_call('GET', '/project/<project>/nodes')
def list_project_nodes(project):
    """List all nodes belonging the given project.

    Returns a JSON array of strings representing a list of nodes.

    Example:  '["node1", "node2", "node3"]'
    """
    db = model.Session()
    project = _must_find(db, model.Project, project)
    nodes = project.nodes
    nodes = [n.label for n in nodes]
    return json.dumps(nodes)


@rest_call('GET', '/project/<project>/networks')
def list_project_networks(project):
    """List all private networks the project can access.

    Returns a JSON array of strings representing a list of networks.

    Example:  '["net1", "net2", "net3"]'
    """
    db = model.Session()
    project = _must_find(db, model.Project, project)
    networks = project.networks_access
    networks = [n.label for n in networks]
    return json.dumps(networks)


@rest_call('GET', '/node/<nodename>')
def show_node(nodename):
    """Show details of a node.

    Returns a JSON object representing a node.
    The object will have at least the following fields:
        * "name", the name/label of the node (string).
        * "free", indicates whether the node is free or has been allocated
            to a project.
        * "nics", a list of nics, each represted by a JSON object having
            at least the following fields:
                - "label", the nic's label.
                - "macaddr", the nic's mac address.

    Example:  '{"name": "node1",
                "free": True,
                "nics": [{"label": "nic1", "macaddr": "01:23:45:67:89"},
                         {"label": "nic2", "macaddr": "12:34:56:78:90"}]
               }'
    """
    db = model.Session()
    node = _must_find(db, model.Node, nodename)
    return json.dumps({
        'name': node.label,
        'free': node.project_id is None,
        'nics': [{'label': n.label,
                  'macaddr': n.mac_addr,
                  } for n in node.nics],
    })


@rest_call('GET', '/project/<project>/headnodes')
def list_project_headnodes(project):
    """List all headnodes belonging the given project.

    Returns a JSON array of strings representing a list of headnodes.

    Example:  '["headnode1", "headnode2", "headnode3"]'
    """
    db = model.Session()
    project = _must_find(db, model.Project, project)
    headnodes = project.headnodes
    headnodes = [hn.label for hn in headnodes]
    return json.dumps(headnodes)


@rest_call('GET', '/headnode/<nodename>')
def show_headnode(nodename):
    """Show details of a headnode.

    Returns a JSON object representing a headnode.
    The obect will have at least the following fields:
        * "name", the name/label of the headnode (string).
        * "project", the project to which the headnode belongs.
        * "hnics", a JSON array of hnic labels that are attached to this
            headnode.
        * "vncport", the vnc port that the headnode VM is listening on; this
            value can be None if the VM is powered off or has not been
            created yet.

    Example:  '{"name": "headnode1",
                "project": "project1",
                "hnics": ["hnic1", "hnic2"],
                "vncport": 5900
               }'
    """
    db = model.Session()
    headnode = _must_find(db, model.Headnode, nodename)
    return json.dumps({
        'name': headnode.label,
        'project': headnode.project.label,
        'hnics': [n.label for n in headnode.hnics],
        'vncport': headnode.get_vncport(),
    })


@rest_call('GET', '/headnode_images/')
def list_headnode_images():
    """Show headnode images listed in config file.

    Returns a JSON array of strings representing a list of headnode images.

    Example:  '["headnode1.img", "headnode2.img", "headnode3.img"]'
    """
    valid_imgs = cfg.get('headnode', 'base_imgs')
    valid_imgs = [img.strip() for img in valid_imgs.split(',')]
    return json.dumps(valid_imgs)


    # Console code #
    ################

@rest_call('GET', '/node/<nodename>/console')
def show_console(nodename):
    """Show the contents of the console log."""
    db = model.Session()
    node = _must_find(db, model.Node, nodename)
    log = node.get_console()
    if log is None:
        raise NotFoundError('The console log for %s '
                            'does not exist.' % nodename)
    return log

@rest_call('PUT', '/node/<nodename>/console')
def start_console(nodename):
    """Start logging output from the console."""
    db = model.Session()
    node = _must_find(db, model.Node, nodename)
    node.start_console()

@rest_call('DELETE', '/node/<nodename>/console')
def stop_console(nodename):
    """Stop logging output from the console and delete the log."""
    db = model.Session()
    node = _must_find(db, model.Node, nodename)
    node.stop_console()
    node.delete_console()


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
        raise DuplicateError("%s %s already exists." % (cls.__name__, name))


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
        raise NotFoundError("%s %s does not exist." % (cls.__name__, name))
    return obj

def _namespaced_query(session, obj_outer, cls_inner, name_inner):
    """Helper function to search for subobjects of an object."""
    return session.query(cls_inner) \
        .filter_by(owner = obj_outer) \
        .filter_by(label = name_inner).first()

def _assert_absent_n(session, obj_outer, cls_inner, name_inner):
    """Raises DuplicateError if a "namespaced" object, such as a node's nic, exists.

    Otherwise returns successfully.

    Arguments:

    session - a SQLAlchemy session to use.
    obj_outer - the "owner" object
    cls_inner - the "owned" class
    name_inner - the name of the "owned" object
    """
    obj_inner = _namespaced_query(session, obj_outer, cls_inner, name_inner)
    if obj_inner is not None:
        raise DuplicateError("%s %s on %s %s already exists" %
                             (cls_inner.__name__, name_inner,
                              obj_outer.__class__.__name__, obj_outer.label))

def _must_find_n(session, obj_outer, cls_inner, name_inner):
    """Searches the database for a "namespaced" object, such as a nic on a node.

    Raises NotFoundError if there is none.  Otherwise returns the object.

    Arguments:

    session - a SQLAlchemy session to use.
    obj_outer - the "owner" object
    cls_inner - the "owned" class
    name_inner - the name of the "owned" object
    """
    obj_inner = _namespaced_query(session, obj_outer, cls_inner, name_inner)
    if obj_inner is None:
        raise NotFoundError("%s %s on %s %s does not exist." %
                            (cls_inner.__name__, name_inner,
                             obj_outer.__class__.__name__, obj_outer.label))
    return obj_inner
