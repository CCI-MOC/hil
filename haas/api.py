"""This module provides the HaaS service's public API.

haas.server translates between this and HTTP.

TODO: Spec out and document what sanitization is required.
"""
import model
from haas.config import cfg
import importlib

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


def user_create(username, password):
    """Create user `username`.

    If the user already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.User, username)
    user = model.User(username, password)
    db.add(user)
    db.commit()


def user_delete(username):
    """Delete user `username`

    If the user does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    user = _must_find(db, model.User, username)
    db.delete(user)
    db.commit()


                            # Group Code #
                            ##############

def group_create(groupname):
    """Create group 'groupname'.

    If the group already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Group, groupname)
    group = model.Group(groupname)
    db.add(group)
    db.commit()


def group_delete(groupname):
    """Delete group 'groupname'

    If the group does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    group = _must_find(db, model.Group, groupname)
    db.delete(group)
    db.commit()


def group_add_user(groupname, username):
    """Add a group to a user

    If the group or user does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    user = _must_find(db, model.User, username)
    group = _must_find(db, model.Group, groupname)
    if group in user.groups:
        raise DuplicateError(username)
    user.groups.append(group)
    db.commit()


def group_remove_user(groupname, username):
    """Remove a group from a user

    If the group or user does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    user = _must_find(db, model.User, username)
    group = _must_find(db, model.Group, groupname)
    if group not in user.groups:
        raise NotFoundError(username)
    user.groups.remove(group)
    db.commit()

                            # Project Code #
                            ################

def project_create(projectname, groupname):
    """Create project 'projectname'.

    If the project already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Project, projectname)
    group = _must_find(db, model.Group, groupname)
    project = model.Project(group, projectname)
    db.add(project)
    db.commit()


def project_delete(projectname):
    """Delete project 'projectname'

    If the project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = _must_find(db, model.Project, projectname)
    db.delete(project)
    db.commit()


def project_deploy(projectname):
    """Deploy project 'projectname'

    If the project does not exist, a NotFoundError will be raised.

    TODO: there are other possible errors, document them and how they are
    handled.
    """
    driver_name = cfg.get('general', 'active_switch')
    driver = importlib.import_module('haas.drivers.' + driver_name)

    db = model.Session()
    project = _must_find(db, model.Project, projectname)

    for net in project.networks:
        for nic in net.nics:
            driver.set_access_vlan(int(nic.port.label), net.vlan_no)

    if project.headnode:
        project.headnode.create()
        for hnic in project.headnode.hnics:
            hnic.create()
        project.headnode.start()
    else:
        pass # TODO: at least log this, if not throw an error.

def project_connect_node(projectname, nodename):
    """Add a project 'projectname' to an existing node

    If the node or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = _must_find(db, model.Project, projectname)
    node = _must_find(db, model.Node, nodename)
    project.nodes.append(node)
    db.commit()


def project_detach_node(projectname, nodename):
    """Remove a project 'projectname' from an existing node

    If the node or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = _must_find(db, model.Project, projectname)
    node = _must_find(db, model.Node, nodename)
    if node not in project.nodes:
        raise NotFoundError(projectname)
    project.nodes.remove(node)
    db.commit()



                            # Node Code #
                            #############

def node_register(nodename):
    """Create node 'nodename'.

    If the node already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Node, nodename)
    node = model.Node(nodename)
    db.add(node)
    db.commit()


def node_delete(nodename):
    """Delete node 'nodename'

    If the node does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    node = _must_find(db, model.Node, nodename)
    db.delete(node)
    db.commit()

def node_register_nic(nodename, nic_name, macaddr):
    """Register exitence of nic attached to given node

    If the node does not exist, a NotFoundError will be raised.

    If there is already an nic with that name, a DuplicateError will be raised.
    """
    db = model.Session()
    node = _must_find(db, model.Node, nodename)
    _assert_absent(db, model.Nic, nic_name)
    nic = model.Nic(node, nic_name, macaddr)
    db.add(nic)
    db.commit()

def node_delete_nic(nodename, nic_name):
    """Delete nic with given name.

    If the nic does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    nic = _must_find(db, model.Nic, nic_name)
    if nic.node.label != nodename:
        # We raise a NotFoundError for the following reason: Nic's SHOULD
        # belong to nodes, and thus we SHOULD be doing a search of the nics
        # belonging to the given node.  (In that situation, we will honestly
        # get a NotFoundError.)  We aren't right now, because currently Nic's
        # labels are globally unique.
        raise NotFoundError("Nic: " + nic_name)
    db.delete(nic)
    db.commit()


def node_connect_network(node_label, nic_label, network_label):
    """Connect a physical NIC to a network"""
    db = model.Session()

    node = _must_find(db, model.Node, node_label)
    nic = _must_find(db, model.Nic, nic_label)
    network = _must_find(db, model.Network, network_label)

    if nic.node is not node:
        # XXX: This is arguably misleading at present, but soon we'll want to
        # have nics namespaced by their nodes, so this is what we want in the
        # long term. We should adjust the models such that nic labels are
        # private to a node.
        raise NotFoundError('nic %s on node %s' % (nic_label, node_label))

    if nic.network:
        # The nic is already part of a network; report an error to the user.
        raise DuplicateError('nic %s on node %s is already part of a network' %
                (nic_label, node_label))

    nic.network = network
    db.commit()

def node_detach_network(node_label, nic_label):
    """Detach a physical nic from its network (if any).

    If the nic is not already a member of a network, this function does nothing.
    """
    db = model.Session()

    node = _must_find(db, model.Node, node_label)
    nic = _must_find(db, model.Nic, nic_label)

    if nic.node is not node:
        raise NotFoundError('nic %s on node %s' % (nic_label, node_label))

    if nic.network is None:
        raise NotFoundError('nic %s on node %s is not attached' % (nic_label, node_label))

    nic.network = None
    db.commit()

                            # Head Node Code #
                            ##################
def headnode_create(nodename, projectname):
    """Create head node 'nodename'.

    If the node already exists, a DuplicateError will be raised.
    """
    db = model.Session()

    _assert_absent(db, model.Headnode, nodename)
    project = _must_find(db, model.Project, projectname)

    if project.headnode is not None:
        raise DuplicateError('project %s already has a headnode' % (projectname))

    headnode = model.Headnode(project, nodename)

    db.add(headnode)
    db.commit()


def headnode_delete(nodename):
    """Delete node 'nodename'

    If the node does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    headnode = _must_find(db, model.Headnode, nodename)
    db.delete(headnode)
    db.commit()

def headnode_create_hnic(nodename, hnic_name, macaddr):
    """Create hnic attached to given headnode

    If the node does not exist, a NotFoundError will be raised.

    If there is already an hnic with that name, a DuplicateError will be raised.
    """
    db = model.Session()
    headnode = _must_find(db, model.Headnode, nodename)
    _assert_absent(db, model.Hnic, hnic_name)
    hnic = model.Hnic(headnode, hnic_name, macaddr)
    db.add(hnic)
    db.commit()

def headnode_delete_hnic(nodename, hnic_name):
    """Delete hnic with given name.

    If the hnic does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    hnic = _must_find(db, model.Hnic, hnic_name)
    if hnic.headnode.label != nodename:
        # We raise a NotFoundError for the following reason: Hnic's SHOULD
        # belong to headnodes, and thus we SHOULD be doing a search of the
        # hnics belonging to the given headnode.  (In that situation, we will
        # honestly get a NotFoundError.)  We aren't right now, because
        # currently Hnic's labels are globally unique.
        raise NotFoundError("Hnic: " + hnic_name)
    db.delete(hnic)
    db.commit()

def headnode_connect_network(node_label, nic_label, network_label):
    """Connect a headnode's NIC to a network"""
    # XXX: This is flagrantly copy/pasted from node_connect network. I feel a
    # little bad about myself, and we should fix this. same goes for
    # *_detach_network.
    db = model.Session()

    headnode = _must_find(db, model.Headnode, node_label)
    hnic = _must_find(db, model.Hnic, nic_label)
    network = _must_find(db, model.Network, network_label)

    if hnic.headnode is not headnode:
        # XXX: This is arguably misleading at present, but soon we'll want to
        # have nics namespaced by their nodes, so this is what we want in the
        # long term. We should adjust the models such that nic labels are
        # private to a node.
        raise NotFoundError('hnic %s on headnode %s' % (nic_label, node_label))

    if hnic.network:
        # The nic is already part of a network; report an error to the user.
        raise DuplicateError('hnic %s on headnode %s is already part of a network' %
                (nic_label, node_label))
    hnic.network = network
    db.commit()

def headnode_detach_network(node_label, nic_label):
    """Detach a heanode's nic from its network (if any).

    If the nic is not already a member of a network, this function does nothing.
    """
    db = model.Session()

    headnode = _must_find(db, model.Headnode, node_label)
    hnic = _must_find(db, model.Hnic, nic_label)

    if hnic.headnode is not headnode:
        raise NotFoundError('hnic %s on headnode %s' % (nic_label, node_label))

    if hnic.network is None:
        raise NotFoundError('hnic %s on headnode %s not attached'
                            % (nic_label, node_label))

    hnic.network = None
    db.commit()

                            # Network Code #
                            ################

def network_create(networkname, projectname):
    """Create network 'networkname'.

    If the network already exists, a DuplicateError will be raised.
    If the network cannot be allocated (due to resource exhaustion), an
    AllocationError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Network, networkname)
    project = _must_find(db, model.Project, projectname)
    vlan = db.query(model.Vlan).filter_by(available=True).first()
    if vlan is None:
        raise AllocationError('No more networks')
    network = model.Network(project, vlan, networkname)
    db.add(network)
    db.commit()


def network_delete(networkname):
    """Delete network 'networkname'

    If the network does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    network = _must_find(db, model.Network, networkname)
    vlan = db.query(model.Vlan).filter_by(vlan_no=network.vlan_no).one()
    vlan.available = True
    db.delete(network)
    db.commit()

                            # Switch code #
                            ###############

def switch_register(name, driver):
    """Register the switch named `name`.

    If the switch already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Switch, name)
    switch = model.Switch(name, driver)
    db.add(switch)
    db.commit()


def switch_delete(name):
    db = model.Session()
    switch = _must_find(db, model.Switch, name)
    db.delete(switch)
    db.commit()


def vlan_register(vlan):
    """Registers the vlan with vlan number `vlan`.

    Note that vlan should be a *string*, not a number. It is intended to be
    pulled right from the HTTP request; this function will validate the
    argument.
    """
    try:
        vlan_no = int(vlan)
    except Exception:
        raise BadArgumentError('vlan:%s' % vlan)
    if vlan_no < 1 or vlan_no > 4096:
        raise BadArgumentError('vlan out of range: %d', vlan_no)
    db = model.Session()
    _assert_absent(db, model.Vlan, str(vlan_no))
    db.add(model.Vlan(vlan_no))
    db.commit()


def vlan_delete(vlan):
    """Deletes the vlan with vlan number `vlan`.

    Note that vlan should be a *string*, not a number. It is intended to be
    pulled right from the HTTP request; this function will validate the
    argument.
    """
    try:
        vlan_no = int(vlan)
    except Exception:
        raise BadArgumentError('vlan:%s' % vlan)
    if vlan_no < 1 or vlan_no > 4096:
        raise BadArgumentError('vlan out of range: %d', vlan_no)

    db = model.Session()
    db.delete(_must_find(db, model.Vlan, str(vlan_no)))
    db.commit()


                            # Switch code #
                            ###############

def switch_register(name, driver):
    """Register the switch named `name`.

    If the switch already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Switch, name)
    switch = model.Switch(name, driver)
    db.add(switch)
    db.commit()

def switch_delete(name):
    db = model.Session()
    switch = _must_find(db, model.Switch, name)
    db.delete(switch)
    db.commit()

def port_register(switch_name, port_name):
    """Register a port with name "port" on switch "switch".

    Currently, this label both must be unique AND will generally have to be
    decimal integers.  This is nonsense if there are multiple switches, but we
    don't support that anyways.

    If the port already exists, a DuplicateError will be raised.

    If the switch does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    switch = _must_find(db, model.Switch, switch_name)
    _assert_absent(db, model.Port, port_name)
    port = model.Port(switch, port_name)
    db.add(port)
    db.commit()

def port_delete(switch_name, port_name):
    """Delete a port with name "port" on switch "switch".

    If the port does not exist, or if the switch does not exist, a
    NotFoundError will be raised.
    """
    db = model.Session()
    switch = _must_find(db, model.Switch, switch_name)
    port = _must_find(db, model.Port, port_name)
    if port.switch is not switch:
        raise NotFoundError(port_name)
    db.delete(port)
    db.commit()


def port_connect_nic(switch_name, port_name, node_name, nic_name):
    """Connect a port on a switch to a nic on a node

    If any of the four arguments does not exist, a NotFoundError will be
    raised.

    If the port or the nic are already connected to something, a
    DuplicateError will be raised.
    """
    db = model.Session()

    switch = _must_find(db, model.Switch, switch_name)
    port = _must_find(db, model.Port, port_name)
    if port.switch is not switch:
        raise NotFoundError(port_name)

    node = _must_find(db, model.Node, node_name)
    nic = _must_find(db, model.Nic, nic_name)
    if nic.node is not node:
        raise NotFoundError(nic_name)

    if nic.port is not None:
        raise DuplicateError(nic_name)

    if port.nic is not None:
        raise DuplicateError(port_name)

    nic.port = port
    db.commit()

def port_detach_nic(switch_name, port_name):
    """Detach attached nic from a port

    If the port or switch are not found, a NotFoundError will be raised.

    If the port is not connected to anything, a NotFoundError will be raised.
    """
    db = model.Session()

    switch = _must_find(db, model.Switch, switch_name)
    port = _must_find(db, model.Port, port_name)
    if port.switch is not switch:
        raise NotFoundError(port_name)


    if port.nic is None:
        raise NotFoundError(port_name)

    port.nic = None
    db.commit()

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
    obj = session.query(cls).filter_by(label = name).first()
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
    obj = session.query(cls).filter_by(label = name).first()
    if not obj:
        raise NotFoundError(cls.__name__ + ': ' + name)
    return obj
