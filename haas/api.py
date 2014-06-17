"""This module provides the HaaS service's public API.

haas.api_server translates between this and HTTP.

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


def group_connect_project(groupname, projectname):
    """Add a project 'projectname' to an existing group

    If the group or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = _must_find(db, model.Project, projectname)
    group = _must_find(db, model.Group, groupname)
    if project in group.projects:
        raise DuplicateError(projectname)
    group.projects.append(project)
    db.commit()


def group_detach_project(groupname, projectname):
    """Remove a project 'projectname' from an existing group

    If the group or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = _must_find(db, model.Project, projectname)
    group = _must_find(db, model.Group, groupname)
    if project not in group.projects:
        raise NotFoundError(projectname)
    project.group = None
    db.commit()


                            # Project Code #
                            ################

def project_create(projectname):
    """Create project 'projectname'.

    If the project already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Project, projectname)
    project = model.Project(projectname)
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


def project_connect_node(projectname, nodename):
    """Add a project 'projectname' to an existing node

    If the node or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = _must_find(db, model.Project, projectname)
    node = _must_find(db, model.Node, nodename)
    if node.projects(project):
        raise DuplicateError(projectname)
    project.node.append(node)
    db.commit()


def project_detach_node(projectname, nodename):
    """Remove a project 'projectname' from an existing node

    If the node or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = _must_find(db, model.Project, projectname)
    node = _must_find(db, model.Node, nodename)
    if not node.projects(project):
        raise NotFoundError(projectname)
    project.node.remove(node)
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
def headnode_create(nodename, projectname):
    """Create head node 'nodename'.

    If the node already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Headnode, nodename)
    headnode = model.Headnode(nodename)

    ## look for group, if it exists assign it
    project = _must_find(db, model.Project, projectname)
    headnode.project = project

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




                            # Network Code #
                            ################

def network_create(networkname):
    """Create network 'networkname'.

    If the network already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    _assert_absent(db, model.Network, networkname)
    network = model.Network(networkname)
    db.add(network)
    db.commit()


def network_delete(networkname):
    """Delete network 'networkname'

    If the network does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    network = _must_find(db, model.Network, networkname)
    db.delete(network)
    db.commit()

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
