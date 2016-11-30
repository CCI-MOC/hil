# 2013-2014 Massachusetts Open Cloud Contributors
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
import json

from schema import Schema, Optional

from haas import model
from haas.model import db
from haas.auth import get_auth_backend
from haas.config import cfg
from haas.rest import rest_call
from haas.class_resolver import concrete_class_for
from haas.network_allocator import get_network_allocator
from haas.errors import *


# Project Code #
################
@rest_call('GET', '/projects', Schema({}))
def list_projects():
    """List all projects.

    Returns a JSON array of strings representing a list of projects.

    Example:  '["project1", "project2", "project3"]'
    """
    get_auth_backend().require_admin()
    projects = model.Project.query.all()
    projects = sorted([p.label for p in projects])
    return json.dumps(projects)


@rest_call('PUT', '/project/<project>', Schema({'project': basestring}))
def project_create(project):
    """Create a project.

    If the project already exists, a DuplicateError will be raised.
    """
    get_auth_backend().require_admin()
    _assert_absent(model.Project, project)
    project = model.Project(project)
    db.session.add(project)
    db.session.commit()


@rest_call('DELETE', '/project/<project>', Schema({'project': basestring}))
def project_delete(project):
    """Delete project.

    If the project does not exist, a NotFoundError will be raised.
    """
    get_auth_backend().require_admin()
    project = _must_find(model.Project, project)
    if project.nodes:
        raise BlockedError("Project has nodes still")
    if project.networks_created:
        raise BlockedError("Project still has networks")
    if project.networks_access:
        # FIXME: This is not the user's fault, and they cannot fix it.  The
        # only reason we need to error here is that, with how network access
        # is done, the following bad thing happens.  If there's a network
        # that only the project can access, its "access" field will be the
        # project.  When you then delete that project, "access" will be set
        # to None instead.  Counter-intuitively, this then makes that
        # network accessible to ALL PROJECTS!  Once we use real ACLs, this
        # will not be an issue---instead, the network will be accessible by
        # NO projects.
        raise BlockedError("Project can still access networks")
    if project.headnodes:
        raise BlockedError("Project still has a headnode")
    db.session.delete(project)
    db.session.commit()


@rest_call('POST', '/project/<project>/connect_node', Schema({
    'project': basestring, 'node': basestring,
}))
def project_connect_node(project, node):
    """Add a node to a project.

    If the node or project does not exist, a NotFoundError will be raised.

    If node is already owned by a project, a BlockedError will be raised.
    """
    project = _must_find(model.Project, project)
    get_auth_backend().require_project_access(project)
    node = _must_find(model.Node, node)
    if node.project is not None:
        raise BlockedError("Node is already owned by a project.")
    project.nodes.append(node)
    db.session.commit()


@rest_call('POST', '/project/<project>/detach_node', Schema({
    'project': basestring, 'node': basestring,
}))
def project_detach_node(project, node):
    """Remove a node from a project.

    If the node or project does not exist, a NotFoundError will be raised.

    If the node has network attachments or pending network actions, a
    BlockedError will be raised.
    """
    project = _must_find(model.Project, project)
    get_auth_backend().require_project_access(project)
    node = _must_find(model.Node, node)
    if node not in project.nodes:
        raise NotFoundError("Node not in project")
    num_attachments = model.NetworkAttachment.query \
        .filter(model.Nic.owner == node,
                model.NetworkAttachment.nic_id == model.Nic.id).count()
    if num_attachments != 0:
        raise BlockedError("Node attached to a network")
    for nic in node.nics:
        if nic.current_action is not None:
            raise BlockedError("Node has pending network actions")
    node.obm.stop_console()
    node.obm.delete_console()
    project.nodes.remove(node)
    db.session.commit()


@rest_call('PUT', '/network/<network>/access/<project>', Schema({
    'project': basestring, 'network': basestring,
}))
def network_grant_project_access(project, network):
    """Add access to <network> to <project>.

    If the project or network does not exist, a NotFoundError will be raised.
    If the project already has access to the network a DuplicateError will be
    raised.
    """
    network = _must_find(model.Network, network)
    project = _must_find(model.Project, project)
    auth_backend = get_auth_backend()

    # Must be admin or the owner of the network to add projects
    if network.owner is None:
        auth_backend.require_admin()
    else:
        auth_backend.require_project_access(network.owner)

    if project in network.access:
        raise DuplicateError('Network %s is already in project %s' %
                             (network.label, project.label))

    network.access.append(project)
    db.session.commit()


@rest_call('DELETE', '/network/<network>/access/<project>', Schema({
    'project': basestring, 'network': basestring,
}))
def network_revoke_project_access(project, network):
    """Remove access to <network> from <project>.

    If the project or network does not exist, a NotFoundError will be raised.
    If the project is the owner of the network a BlockedError will be raised.
    """
    auth_backend = get_auth_backend()
    network = _must_find(model.Network, network)
    project = _must_find(model.Project, project)
    # must be admin, the owner of the network, or <project> to remove
    # <project>.

    if network.access:
        if not (auth_backend.have_admin() or
                (network.owner is not None and
                    auth_backend.have_project_access(network.owner)) or
                (project in network.access and
                    auth_backend.have_project_access(project))):
            raise AuthorizationError("You are not authorized to remove the "
                                     "specified project from this network.")

    if project not in network.access:
        raise NotFoundError("Network %r is not in project %r" %
                            (network.label, project.label))

    if project is network.owner:
        raise BlockedError("Project %r is owner of network %r and "
                           "its access cannot be removed" %
                           (project.label, network.label))

    # TODO: Make this and the next loop more SQLAlchemy-friendly
    for attachment in network.attachments:
        if attachment.nic.owner.project.label == project.label:
            raise BlockedError(
                "Project still has node(s) attached to the network")

    for hnic in network.hnics:
        if hnic.owner.project.label == project.label:
            raise BlockedError(
                "Project still has headnode(s) attached to the network")

    network.access.remove(project)
    db.session.commit()


# Node Code #
#############
@rest_call('PUT', '/node/<node>', schema=Schema({
    'node': basestring,
    'obm': {
        'type': basestring,
        Optional(object): object,
    },
    Optional('metadata'): object,
}))
def node_register(node, **kwargs):
    """Create node.

    If the node already exists, a DuplicateError will be raised.
    The node is initially registered with no nics; see the method
    node_register_nic.
    """
    get_auth_backend().require_admin()
    _assert_absent(model.Node, node)
    obm_type = kwargs['obm']['type']
    cls = concrete_class_for(model.Obm, obm_type)
    if cls is None:
        raise BadArgumentError('%r is not a valid OBM type.' % obm_type)
    cls.validate(kwargs['obm'])
    node_obj = model.Node(label=node, obm=cls(**kwargs['obm']))
    if 'metadata' in kwargs:
        for label, value in kwargs['metadata'].items():
            metadata_obj = model.Metadata(label, json.dumps(value), node_obj)
            db.session.add(metadata_obj)
    db.session.add(node_obj)
    db.session.commit()


@rest_call('POST', '/node/<node>/power_cycle', Schema({'node': basestring}))
def node_power_cycle(node):
    auth_backend = get_auth_backend()
    node = _must_find(model.Node, node)
    if node.project is None:
        auth_backend.require_admin()
    else:
        auth_backend.require_project_access(node.project)
    node.obm.power_cycle()


@rest_call('POST', '/node/<node>/power_off', Schema({'node': basestring}))
def node_power_off(node):
    auth_backend = get_auth_backend()
    node = _must_find(model.Node, node)
    if node.project is None:
        auth_backend.require_admin()
    else:
        auth_backend.require_project_access(node.project)
    node.obm.power_off()


@rest_call('DELETE', '/node/<node>', Schema({'node': basestring}))
def node_delete(node):
    """Delete node.

    If the node does not exist, a NotFoundError will be raised.
    """
    get_auth_backend().require_admin()
    node = _must_find(model.Node, node)
    if node.nics != []:
        raise BlockedError("Node %r has nics; remove them before deleting %r."
                           % (node.label, node.label))
    node.obm.stop_console()
    node.obm.delete_console()
    db.session.delete(node)
    db.session.commit()


@rest_call('PUT', '/node/<node>/nic/<nic>', Schema({
    'node': basestring, 'nic': basestring, 'macaddr': basestring,
}))
def node_register_nic(node, nic, macaddr):
    """Register existence of nic attached to given node.

    If the node does not exist, a NotFoundError will be raised.

    If there is already an nic with that name, a DuplicateError will be raised.
    """
    get_auth_backend().require_admin()
    node = _must_find(model.Node, node)
    _assert_absent_n(node, model.Nic, nic)
    nic = model.Nic(node, nic, macaddr)
    db.session.add(nic)
    db.session.commit()


@rest_call('DELETE', '/node/<node>/nic/<nic>', Schema({
    'node': basestring, 'nic': basestring,
}))
def node_delete_nic(node, nic):
    """Delete nic with given name from it's node.

    If the node or nic does not exist, a NotFoundError will be raised.
    """
    get_auth_backend().require_admin()
    nic = _must_find_n(_must_find(model.Node, node), model.Nic, nic)
    db.session.delete(nic)
    db.session.commit()


@rest_call('POST', '/node/<node>/nic/<nic>/connect_network', schema=Schema({
    'node': basestring,
    'nic': basestring,
    'network': basestring,
    Optional('channel'): basestring,
}))
def node_connect_network(node, nic, network, channel=None):
    """Connect a physical NIC to a network, on channel.

    If channel is ``None``, use the allocator default.

    Raises ProjectMismatchError if the node is not in a project, or if the
    project does not have access rights to the given network.

    Raises BlockedError if there is a pending network action, or if the network
    is already attached to the nic, or if the channel is in use.

    Raises BadArgumentError if the channel is invalid for the network.
    """

    def _have_attachment(nic, query):
        """Return whether there are any attachments matching ``query`` for ``nic``.

        ``query`` should an argument suitable to pass to db.query(...).filter
        """
        return model.NetworkAttachment.query.filter(
            model.NetworkAttachment.nic == nic,
            query,
        ).count() != 0

    auth_backend = get_auth_backend()

    node = _must_find(model.Node, node)
    nic = _must_find_n(node, model.Nic, nic)
    network = _must_find(model.Network, network)

    if not node.project:
        raise ProjectMismatchError("Node not in project")
    auth_backend.require_project_access(node.project)

    project = node.project

    allocator = get_network_allocator()

    if nic.port is None:
        raise NotFoundError("No port is connected to given nic.")

    if nic.current_action:
        raise BlockedError(
            "A networking operation is already active on the nic.")

    if (network.access) and (project not in network.access):
        raise ProjectMismatchError(
            "Project does not have access to given network.")

    if _have_attachment(nic, model.NetworkAttachment.network == network):
        raise BlockedError("The network is already attached to the nic.")

    if channel is None:
        channel = allocator.get_default_channel()

    if _have_attachment(nic, model.NetworkAttachment.channel == channel):
        raise BlockedError("The channel is already in use on the nic.")

    if not allocator.is_legal_channel_for(channel, network.network_id):
        raise BadArgumentError("Channel %r, is not legal for this network." %
                               channel)

    db.session.add(model.NetworkingAction(nic=nic,
                                          new_network=network,
                                          channel=channel))
    db.session.commit()
    return '', 202


@rest_call('POST', '/node/<node>/nic/<nic>/detach_network', Schema({
    'node': basestring, 'nic': basestring, 'network': basestring,
}))
def node_detach_network(node, nic, network):
    """Detach network ``network`` from physical nic ``nic``.

    Raises ProjectMismatchError if the node is not in a project.

    Raises BlockedError if there is already a pending network action.

    Raises BadArgumentError if the network is not attached to the nic.
    """
    auth_backend = get_auth_backend()

    node = _must_find(model.Node, node)
    network = _must_find(model.Network, network)
    nic = _must_find_n(node, model.Nic, nic)

    if not node.project:
        raise ProjectMismatchError("Node not in project")
    auth_backend.require_project_access(node.project)

    if nic.current_action:
        raise BlockedError(
            "A networking operation is already active on the nic.")
    attachment = model.NetworkAttachment.query \
        .filter_by(nic=nic, network=network).first()
    if attachment is None:
        raise BadArgumentError("The network is not attached to the nic.")
    db.session.add(model.NetworkingAction(nic=nic,
                                          channel=attachment.channel,
                                          new_network=None))
    db.session.commit()
    return '', 202


@rest_call('PUT', '/node/<node>/metadata/<label>', Schema({
    'node': basestring, 'label': basestring, 'value': object,
}))
def node_set_metadata(node, label, value):
    """Register metadata on a node.

    If the label already exists, the value will be updated.
    """
    get_auth_backend().require_admin()
    node = _must_find(model.Node, node)
    obj_inner = _namespaced_query(node, model.Metadata, label)
    if obj_inner is not None:
        metadata = _must_find_n(node, model.Metadata, label)
        metadata.value = json.dumps(value)
    else:
        metadata = model.Metadata(label, json.dumps(value), node)
        db.session.add(metadata)
    db.session.commit()


@rest_call('DELETE', '/node/<node>/metadata/<label>', Schema({
    'node': basestring, 'label': basestring,
}))
def node_delete_metadata(node, label):
    """Delete a metadata from a node.

    If the metadata does not exist, a NotFoundError will be raised.
    """
    get_auth_backend().require_admin()
    node = _must_find(model.Node, node)
    metadata = _must_find_n(node, model.Metadata, label)

    db.session.delete(metadata)
    db.session.commit()


# Head Node Code #
##################
@rest_call('PUT', '/headnode/<headnode>', Schema({
    'headnode': basestring, 'project': basestring, 'base_img': basestring,
}))
def headnode_create(headnode, project, base_img):
    """Create headnode.

    If a headnode with the same name already exists, a DuplicateError will be
    raised.

    If the project does not exist, a NotFoundError will be raised.

    If the base image does not exist (is not specified in haas.cfg) a
    BadArgumentError will be raised.
    """

    valid_imgs = cfg.get('headnode', 'base_imgs')
    valid_imgs = [img.strip() for img in valid_imgs.split(',')]

    if base_img not in valid_imgs:
        raise BadArgumentError('Provided image is not a valid image.')

    _assert_absent(model.Headnode, headnode)
    project = _must_find(model.Project, project)
    get_auth_backend().require_project_access(project)

    headnode = model.Headnode(project, headnode, base_img)

    db.session.add(headnode)
    db.session.commit()


@rest_call('DELETE', '/headnode/<headnode>', Schema({'headnode': basestring}))
def headnode_delete(headnode):
    """Delete headnode.

    If the node does not exist, a NotFoundError will be raised.
    """
    headnode = _must_find(model.Headnode, headnode)
    get_auth_backend().require_project_access(headnode.project)
    if not headnode.dirty:
        headnode.delete()
    for hnic in headnode.hnics:
        db.session.delete(hnic)
    db.session.delete(headnode)
    db.session.commit()


@rest_call('POST', '/headnode/<headnode>/start', Schema({
    'headnode': basestring,
}))
def headnode_start(headnode):
    """Start the headnode.

    This actually boots up the headnode virtual machine. The VM is created
    within libvirt if needed. Once the VM has been started once, it is
    "frozen," and all other headnode-related api calls will fail (by raising
    an IllegalStateError), with the exception of headnode_stop.
    """
    headnode = _must_find(model.Headnode, headnode)
    get_auth_backend().require_project_access(headnode.project)
    if headnode.dirty:
        headnode.create()
    headnode.start()
    db.session.commit()


@rest_call('POST', '/headnode/<headnode>/stop', Schema({
    'headnode': basestring,
}))
def headnode_stop(headnode):
    """Stop the headnode.

    This powers off the headnode. This is a hard poweroff; the VM is not given
    the opportunity to shut down cleanly. This does *not* unfreeze the VM;
    headnode_start will be the only valid API call after the VM is powered off.
    """
    headnode = _must_find(model.Headnode, headnode)
    get_auth_backend().require_project_access(headnode.project)
    headnode.stop()


@rest_call('PUT', '/headnode/<headnode>/hnic/<hnic>', Schema({
    'headnode': basestring, 'hnic': basestring,
}))
def headnode_create_hnic(headnode, hnic):
    """Create hnic attached to given headnode.

    If the node does not exist, a NotFoundError will be raised.

    If there is already an hnic with that name, a DuplicateError will
    be raised.

    If the headnode's VM has already created (headnode is not "dirty"), raises
    an IllegalStateError
    """
    headnode = _must_find(model.Headnode, headnode)
    get_auth_backend().require_project_access(headnode.project)
    _assert_absent_n(headnode, model.Hnic, hnic)

    if not headnode.dirty:
        raise IllegalStateError

    hnic = model.Hnic(headnode, hnic)
    db.session.add(hnic)
    db.session.commit()


@rest_call('DELETE', '/headnode/<headnode>/hnic/<hnic>', Schema({
    'headnode': basestring, 'hnic': basestring,
}))
def headnode_delete_hnic(headnode, hnic):
    """Delete hnic on a given headnode.

    If the headnode or hnic does not exist, a NotFoundError will be raised.

    If the headnode's VM has already created (headnode is not "dirty"), raises
    an IllegalStateError
    """
    headnode = _must_find(model.Headnode, headnode)
    get_auth_backend().require_project_access(headnode.project)
    hnic = _must_find_n(headnode, model.Hnic, hnic)

    if not headnode.dirty:
        raise IllegalStateError

    db.session.delete(hnic)
    db.session.commit()


@rest_call('POST', '/headnode/<headnode>/hnic/<hnic>/connect_network', Schema({
    'headnode': basestring, 'hnic': basestring, 'network': basestring,
}))
def headnode_connect_network(headnode, hnic, network):
    """Connect a headnode's hnic to a network.

    Raises IllegalStateError if the headnode has already been started.

    Raises ProjectMismatchError if the project does not have access rights to
    the given network.

    Raises BadArgumentError if the network is a non-allocated network. This
    is currently unsupported due to an implementation limitation, but will be
    supported in a future release. See issue #333.
    """
    headnode = _must_find(model.Headnode, headnode)
    get_auth_backend().require_project_access(headnode.project)
    hnic = _must_find_n(headnode, model.Hnic, hnic)
    network = _must_find(model.Network, network)

    if not network.allocated:
        raise BadArgumentError("Headnodes may only be connected to networks "
                               "allocated by the project.")

    if not headnode.dirty:
        raise IllegalStateError

    project = headnode.project

    if (network.access) and (project not in network.access):
        raise ProjectMismatchError(
            "Project does not have access to given network.")

    hnic.network = network
    db.session.commit()


@rest_call('POST', '/headnode/<headnode>/hnic/<hnic>/detach_network', Schema({
    'headnode': basestring, 'hnic': basestring,
}))
def headnode_detach_network(headnode, hnic):
    """Detach a heanode's nic from any network it's on.

    Raises IllegalStateError if the headnode has already been started.
    """
    headnode = _must_find(model.Headnode, headnode)
    get_auth_backend().require_project_access(headnode.project)
    hnic = _must_find_n(headnode, model.Hnic, hnic)

    if not headnode.dirty:
        raise IllegalStateError

    hnic.network = None
    db.session.commit()


# Network Code #
################

@rest_call('GET', '/networks', Schema({}))
def list_networks():
    """Lists all networks"""

    get_auth_backend().require_admin()

    networks = db.session.query(model.Network).all()
    result = {}
    for n in networks:
        if n.access:
            net = {'network_id': n.network_id,
                   'projects': sorted([p.label for p in n.access])}
        else:
            net = {'network_id': n.network_id, 'projects': None}
        result[n.label] = net

    return json.dumps(result, sort_keys=True)


@rest_call('GET', '/network/<network>/attachments', schema=Schema({
    'network': basestring, Optional('project'): basestring,
}))
def list_network_attachments(network, project=None):
    """Lists all the attachments from <project> for <network>

    If <project> is `None`, lists all attachments for <network>
    """
    auth_backend = get_auth_backend()
    network = _must_find(model.Network, network)

    # Determine if caller has access to owning project
    if network.owner is None:
        owner_access = auth_backend.have_admin()
    else:
        owner_access = auth_backend.have_project_access(network.owner)

    if project is None:
        # No project means list all connected nodes
        # Only access to the project that owns the network or an admin can do
        # this
        if not owner_access:
            raise AuthorizationError("Operation requires admin rights or"
                                     " access to network's owning project")
    else:
        # Only list the nodes coming from the specified project that are
        # connected to this network.
        project = _must_find(model.Project, project)
        if not owner_access:
            # Caller does not own the network, so they need both basic access
            # to the network, and access to tueh queried project.
            if not (project in network.access and
                    auth_backend.have_project_access(project)):
                raise AuthorizationError(
                    "You do not have access to this project.")

    attachments = network.attachments
    nodes = {}
    for attachment in attachments:
        if project is None or project is attachment.nic.owner.project:
            node = {
                'nic': attachment.nic.label,
                'channel': attachment.channel,
                'project': attachment.nic.owner.project.label
            }
            nodes[attachment.nic.owner.label] = node

    return json.dumps(nodes, sort_keys=True)


@rest_call('PUT', '/network/<network>', Schema({
    'network': basestring,
    'owner': basestring,
    'access': basestring,
    'net_id': basestring,
}))
def network_create(network, owner, access, net_id):
    """Create a network.

    If the network with that name already exists, a DuplicateError will be
    raised.

    If the combination of owner, access, and net_id is illegal, a
    BadArgumentError will be raised.

    If network ID allocation was requested, and the network cannot be
    allocated (due to resource exhaustion), an AllocationError will be raised.

    Pass 'admin' as owner for an administrator-owned network.  Pass '' as
    access for a publicly accessible network.  Pass '' as net_id if you wish
    to use the HaaS's network-id allocation pool.

    Details of the various combinations of network attributes are in
    docs/networks.md
    """
    auth_backend = get_auth_backend()
    _assert_absent(model.Network, network)

    # Check authorization and legality of arguments, and find correct 'access'
    # and 'owner'
    if owner != "admin":
        owner = _must_find(model.Project, owner)
        auth_backend.require_project_access(owner)
        # Project-owned network
        if access != owner.label:
            raise BadArgumentError(
                "Project-owned networks must be accessible by the owner.")
        if net_id != "":
            raise BadArgumentError(
                "Project-owned networks must use network ID allocation")
        access = [_must_find(model.Project, access)]
    else:
        # Administrator-owned network
        auth_backend.require_admin()
        owner = None
        if access == "":
            access = []
        else:
            access = [_must_find(model.Project, access)]

    # Allocate net_id, if requested
    if net_id == "":
        net_id = get_network_allocator().get_new_network_id()
        if net_id is None:
            raise AllocationError('No more networks')
        allocated = True
    else:
        if not get_network_allocator().validate_network_id(net_id):
            raise BadArgumentError("Invalid net_id")
        allocated = False

    network = model.Network(owner, access, allocated, net_id, network)
    db.session.add(network)
    db.session.commit()


@rest_call('DELETE', '/network/<network>', Schema({'network': basestring}))
def network_delete(network):
    """Delete network.

    If the network does not exist, a NotFoundError will be raised.

    If the network is connected to nodes or headnodes, or there are pending
    network actions involving it, a BlockedError will be raised.
    """
    auth_backend = get_auth_backend()

    network = _must_find(model.Network, network)

    if network.owner is None:
        auth_backend.require_admin()
    else:
        auth_backend.require_project_access(network.owner)

    if len(network.attachments) != 0:
        raise BlockedError("Network still connected to nodes")
    if network.hnics:
        raise BlockedError("Network still connected to headnodes")
    if len(network.scheduled_nics) != 0:
        raise BlockedError("There are pending actions on this network")
    if network.allocated:
        get_network_allocator().free_network_id(network.network_id)

    db.session.delete(network)
    db.session.commit()


@rest_call('GET', '/network/<network>', Schema({'network': basestring}))
def show_network(network):
    """Show details of a network.

    Returns a JSON object representing a network. See `docs/rest_api.md`
    for a full description of the output.
    """
    allocator = get_network_allocator()
    auth_backend = get_auth_backend()

    network = _must_find(model.Network, network)

    if network.access:
        authorized = False
        for proj in network.access:
            authorized = authorized or auth_backend.have_project_access(proj)

        if not authorized:
            raise AuthorizationError("You do not have access to this network.")

    result = {
        'name': network.label,
        'channels': allocator.legal_channels_for(network.network_id),
    }
    if network.owner is None:
        result['owner'] = 'admin'
    else:
        result['owner'] = network.owner.label

    if network.access:
        result['access'] = [p.label for p in network.access]
    else:
        result['access'] = None

    return json.dumps(result, sort_keys=True)


@rest_call('PUT', '/switch/<switch>', schema=Schema({
    'switch': basestring,
    'type': basestring,
    Optional(object): object,
}))
def switch_register(switch, type, **kwargs):
    get_auth_backend().require_admin()
    _assert_absent(model.Switch, switch)

    cls = concrete_class_for(model.Switch, type)
    if cls is None:
        raise BadArgumentError('%r is not a valid switch type.' % type)
    cls.validate(kwargs)
    obj = cls(**kwargs)
    obj.label = switch
    obj.type = type

    db.session.add(obj)
    db.session.commit()


@rest_call('DELETE', '/switch/<switch>', Schema({'switch': basestring}))
def switch_delete(switch):
    get_auth_backend().require_admin()
    switch = _must_find(model.Switch, switch)

    if switch.ports != []:
        raise BlockedError("Switch %r has ports; delete them first." %
                           switch.label)

    db.session.delete(switch)
    db.session.commit()


@rest_call('PUT', '/switch/<switch>/port/<path:port>', Schema({
    'switch': basestring, 'port': basestring,
}))
def switch_register_port(switch, port):
    """Register a port on a switch.

    If the port already exists, a DuplicateError will be raised.
    """
    get_auth_backend().require_admin()
    switch = _must_find(model.Switch, switch)
    _assert_absent_n(switch, model.Port, port)
    port = model.Port(port, switch)

    db.session.add(port)
    db.session.commit()


@rest_call('DELETE', '/switch/<switch>/port/<path:port>', Schema({
    'switch': basestring, 'port': basestring,
}))
def switch_delete_port(switch, port):
    """Delete a port on a switch.

    If the port does not exist, a NotFoundError will be raised.
    """
    get_auth_backend().require_admin()
    switch = _must_find(model.Switch, switch)
    port = _must_find_n(switch, model.Port, port)
    if port.nic is not None:
        raise BlockedError("Port %r is attached to a nic; please detach "
                           "it first." % port.label)

    db.session.delete(port)
    db.session.commit()


@rest_call('GET', '/switch/<switch>', Schema({
    'switch': basestring,
}))
def show_switch(switch):
    """Show details of a switch.

    Returns a JSON object regrading the switch. See `docs/rest_api.md`
    for a full description of the output.

    FIXME: Ideally this api call should return all detail information about
    this switch. right now it needs support from the switch backend.
    """
    get_auth_backend().require_admin()
    switch = _must_find(model.Switch, switch)

    return json.dumps({
        'name': switch.label,
        'ports': [{'label': port.label}
                  for port in switch.ports],
    }, sort_keys=True)


@rest_call('GET', '/switches', Schema({}))
def list_switches():
    """List all switches.

    Returns a JSON array of strings representing a list of switches.

    Example:  '["cisco3", "brocade1", "mock2"]'
    """
    get_auth_backend().require_admin()
    switches = model.Switch.query.all()
    snames = sorted([s.label for s in switches])
    return json.dumps(snames)


@rest_call('POST', '/switch/<switch>/port/<path:port>/connect_nic', Schema({
    'switch': basestring,
    'port': basestring,
    'node': basestring,
    'nic': basestring,
}))
def port_connect_nic(switch, port, node, nic):
    """Connect a port on a switch to a nic on a node.

    If any of the three arguments does not exist, a NotFoundError will be
    raised.

    If the port or the nic is already connected to something, a DuplicateError
    will be raised.
    """
    get_auth_backend().require_admin()
    switch = _must_find(model.Switch, switch)
    port = _must_find_n(switch, model.Port, port)

    node = _must_find(model.Node, node)
    nic = _must_find_n(node, model.Nic, nic)

    if nic.port is not None:
        raise DuplicateError(nic.label)

    if port.nic is not None:
        raise DuplicateError(port.label)

    nic.port = port
    db.session.commit()


@rest_call('POST', '/switch/<switch>/port/<path:port>/detach_nic', Schema({
    'switch': basestring, 'port': basestring,
}))
def port_detach_nic(switch, port):
    """Detach a port from the nic it's attached to

    If the port does not exist, a NotFoundError will be raised.

    If the port is not connected to anything, a NotFoundError will be raised.

    If the port is attached to a node which is not free, a BlockedError
    will be raised.
    """
    get_auth_backend().require_admin()
    switch = _must_find(model.Switch, switch)
    port = _must_find_n(switch, model.Port, port)

    if port.nic is None:
        raise NotFoundError(port.label + " not attached")
    if port.nic.owner.project is not None:
        raise BlockedError("The port is attached to a node which is not free")

    port.nic = None
    db.session.commit()


@rest_call('GET', '/nodes/<is_free>', Schema({'is_free': basestring}))
def list_nodes(is_free):
    """List all nodes or all free nodes

    Returns a JSON array of strings representing a list of nodes.

    Example:  '["node1", "node2", "node3"]'
    """
    if is_free == "free":
        nodes = model.Node.query.filter_by(project_id=None).all()
    else:
        nodes = model.Node.query.all()

    nodes = sorted([n.label for n in nodes])
    return json.dumps(nodes)


@rest_call('GET', '/project/<project>/nodes', Schema({'project': basestring}))
def list_project_nodes(project):
    """List all nodes belonging the given project.

    Returns a JSON array of strings representing a list of nodes.

    Example:  '["node1", "node2", "node3"]'
    """
    project = _must_find(model.Project, project)
    get_auth_backend().require_project_access(project)
    nodes = project.nodes
    nodes = [n.label for n in nodes]
    return json.dumps(nodes)


@rest_call('GET', '/project/<project>/networks', Schema({
    'project': basestring,
}))
def list_project_networks(project):
    """List all private networks the project can access.

    Returns a JSON array of strings representing a list of networks.

    Example:  '["net1", "net2", "net3"]'
    """
    project = _must_find(model.Project, project)
    get_auth_backend().require_project_access(project)
    networks = project.networks_access
    networks = sorted([n.label for n in networks])
    return json.dumps(networks)


@rest_call('GET', '/node/<nodename>', Schema({'nodename': basestring}))
def show_node(nodename):
    """Show the details of a node.

    Returns a JSON object representing a node.
    """

    node = _must_find(model.Node, nodename)
    if node.project is not None:
        get_auth_backend().require_project_access(node.project)
    return json.dumps({
        'name': node.label,
        'project': None if node.project_id is None else node.project.label,
        'nics': [{'label': n.label,
                  'macaddr': n.mac_addr,
                  'networks': dict([(attachment.channel,
                                     attachment.network.label)
                                    for attachment in n.attachments]),
                  } for n in node.nics],
        'metadata': {m.label: m.value for m in node.metadata}
    }, sort_keys=True)


@rest_call('GET', '/project/<project>/headnodes', Schema({
    'project': basestring,
}))
def list_project_headnodes(project):
    """List all headnodes belonging the given project.

    Returns a JSON array of strings representing a list of headnodes.

    Example:  '["headnode1", "headnode2", "headnode3"]'
    """
    project = _must_find(model.Project, project)
    get_auth_backend().require_project_access(project)
    headnodes = project.headnodes
    headnodes = sorted([hn.label for hn in headnodes])
    return json.dumps(headnodes)


@rest_call('GET', '/headnode/<nodename>', Schema({
    'nodename': basestring,
}))
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
    headnode = _must_find(model.Headnode, nodename)
    get_auth_backend().require_project_access(headnode.project)
    return json.dumps({
        'name': headnode.label,
        'project': headnode.project.label,
        'hnics': [n.label for n in headnode.hnics],
        'vncport': headnode.get_vncport(),
        'uuid': headnode.uuid,
        'base_img': headnode.base_img,
    }, sort_keys=True)


@rest_call('GET', '/headnode_images/', Schema({}))
def list_headnode_images():
    """Show headnode images listed in config file.

    Returns a JSON array of strings representing a list of headnode images.

    Example:  '["headnode1.img", "headnode2.img", "headnode3.img"]'
    """
    valid_imgs = cfg.get('headnode', 'base_imgs')
    valid_imgs = sorted([img.strip() for img in valid_imgs.split(',')])
    return json.dumps(valid_imgs)


# Console code #
################
@rest_call('GET', '/node/<nodename>/console', Schema({'nodename': basestring}))
def show_console(nodename):
    """Show the contents of the console log."""
    node = _must_find(model.Node, nodename)
    log = node.obm.get_console()
    if log is None:
        raise NotFoundError('The console log for %s '
                            'does not exist.' % nodename)
    return log


@rest_call('PUT', '/node/<nodename>/console', Schema({'nodename': basestring}))
def start_console(nodename):
    """Start logging output from the console."""
    node = _must_find(model.Node, nodename)
    node.obm.start_console()


@rest_call('DELETE', '/node/<nodename>/console', Schema({
    'nodename': basestring,
}))
def stop_console(nodename):
    """Stop logging output from the console and delete the log."""
    node = _must_find(model.Node, nodename)
    node.obm.stop_console()
    node.obm.delete_console()


# Helper functions #
####################
def _assert_absent(cls, name):
    """Raises a DuplicateError if the given object is already in the database.

    This is useful for most of the *_create functions.

    Arguments:

    cls - the class of the object to query.
    name - the name of the object in question.

    Must be called within a request context.
    """
    obj = db.session.query(cls).filter_by(label=name).first()
    if obj:
        raise DuplicateError("%s %s already exists." % (cls.__name__, name))


def _must_find(cls, name):
    """Raises a NotFoundError if the given object doesn't exist in the datbase.
    Otherwise returns the object

    This is useful for most of the *_delete functions.

    Arguments:

    cls - the class of the object to query.
    name - the name of the object in question.

    Must be called within a request context.
    """
    obj = db.session.query(cls).filter_by(label=name).first()
    if not obj:
        raise NotFoundError("%s %s does not exist." % (cls.__name__, name))
    return obj


def _namespaced_query(obj_outer, cls_inner, name_inner):
    """Helper function to search for subobjects of an object."""
    return db.session.query(cls_inner) \
        .filter_by(owner=obj_outer) \
        .filter_by(label=name_inner).first()


def _assert_absent_n(obj_outer, cls_inner, name_inner):
    """Raises DuplicateError if a "namespaced" object, such as a node's nic,
    exists.

    Otherwise returns successfully.

    Arguments:

    obj_outer - the "owner" object
    cls_inner - the "owned" class
    name_inner - the name of the "owned" object

    Must be called within a request context.
    """
    obj_inner = _namespaced_query(obj_outer, cls_inner, name_inner)
    if obj_inner is not None:
        raise DuplicateError("%s %s on %s %s already exists" %
                             (cls_inner.__name__, name_inner,
                              obj_outer.__class__.__name__, obj_outer.label))


def _must_find_n(obj_outer, cls_inner, name_inner):
    """Searches the database for a "namespaced" object, such as a nic on a node.

    Raises NotFoundError if there is none.  Otherwise returns the object.

    Arguments:

    obj_outer - the "owner" object
    cls_inner - the "owned" class
    name_inner - the name of the "owned" object

    Must be called within a request context.
    """
    obj_inner = _namespaced_query(obj_outer, cls_inner, name_inner)
    if obj_inner is None:
        raise NotFoundError("%s %s on %s %s does not exist." %
                            (cls_inner.__name__, name_inner,
                             obj_outer.__class__.__name__, obj_outer.label))
    return obj_inner
