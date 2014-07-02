"""This module provides the HaaS service's public API.

haas.server translates between this and HTTP.

TODO: Spec out and document what sanitization is required.
"""

import model

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
    db = model.Session()
    project = _must_find(db, model.Project, projectname)
    if project.headnode:
        project.headnode.create()
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


def project_connect_network(projectname, networkname):
    """Add a project 'projectname' to an existing network

    If the network or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = _must_find(db, model.Project, projectname)
    network = _must_find(db, model.Network, networkname)
    if network.projects(project):
        raise DuplicateError(projectname)
    project.network.append(network)
    db.commit()


def project_detach_network(projectname, networkname):
    """Remove a project 'projectname' from an existing network

    If the network or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = _must_find(db, model.Project, projectname)
    network = _must_find(db, model.Network, networkname)
    if not network.projects(project):
        raise NotFoundError(projectname)
    project.network.remove(network)
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


                            # Head Node Code #
                            ##################
def headnode_create(nodename, groupname):
    """Create head node 'nodename'.

    If the node already exists, a DuplicateError will be raised.
    """
    db = model.Session()

    _assert_absent(db, model.Headnode, nodename)
    group = _must_find(db, model.Group, groupname)

    headnode = model.Headnode(group, nodename)

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
    group = headnode.group
    _assert_absent(db, model.Hnic, hnic_name)
    hnic = model.Hnic(group, headnode, hnic_name, macaddr)
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

                            # Network Code #
                            ################

def network_create(networkname, groupname):
    """Create network 'networkname'.

    If the network already exists, a DuplicateError will be raised.
    If the network cannot be allocated (due to resource exhaustion), an
    AllocationError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Network, networkname)
    group = _must_find(db, model.Group, groupname)
    vlan = db.query(model.Vlan).filter_by(available=True).first()
    if vlan is None:
        raise AllocationError('No more networks')
    network = model.Network(group, vlan, networkname)
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
