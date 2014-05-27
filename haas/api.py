"""This module provides the HaaS service's public API.

haas.api_server translates between this and HTTP.

TODO: Spec out and document what sanitization is required.
"""

from haas import model

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
    # XXX: This works, but we should probably have the database do the heavy
    # lifting, i.e. try to create a user, and if we get an IntegretyError from
    # sqlalchemy, then pass on the error.
    user = db.query(model.User).filter_by(label = username).first()
    if user:
        raise DuplicateError(username)
    user = model.User(username, password)
    db.add(user)
    db.commit()

def user_delete(username):
    """Delete user `username`

    If the user does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    user = db.query(model.User).filter_by(label = username).first()
    if not user:
        raise NotFoundError(username)
    db.delete(user)
    db.commit()


                            # Group Code #
                            ##############

def group_create(groupname):
    """Create group 'groupname'.

    If the group already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    # XXX: This works, but we should probably have the database do the heavy
    # lifting, i.e. try to create a user, and if we get an IntegretyError from
    # sqlalchemy, then pass on the error.
    group = db.query(model.Group).filter_by(label = groupname).first()
    if group:
        raise DuplicateError(groupname)
    group = model.Group(groupname)
    db.add(group)
    db.commit()

def group_delete(groupname):
    """Delete group 'groupname'

    If the group does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    group = db.query(model.Group).filter_by(label = groupname).first()
    if not group:
        raise NotFoundError(groupname)
    db.delete(group)
    db.commit()

def add_user(groupname, username):
    """Add a group to a user
    
    If the group or user does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    user = db.query(model.User).filter_by(label = username).first()
    if not user:
        raise NotFoundError(username)
    group = db.query(model.Group).filter_by(label = groupname).first()
    if not group:
        raise NotFoundError(groupname)
    if user.groups(group) # if user was already added to group
        raise DuplicateError(username)
    user.groups.append(user)
    db.commit()

def remove_user(groupname, username):
    """Remove a group from a user
    
    If the group or user does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    user = db.query(model.User).filter_by(label = username).first()
    if not user:
        raise NotFoundError(username)
    group = db.query(model.Group).filter_by(label = groupname).first()
    if not group:
        raise NotFoundError(groupname)
    if not user.groups(user) # if user isn't a part of the group
        raise NotFoundError(username)    
    user.groups.remove(user)
    db.commit()



                            # Project Code #
                            ################

def project_create(projectname):
    """Create project 'projectname'.

    If the project already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    # XXX: This works, but we should probably have the database do the heavy
    # lifting, i.e. try to create a user, and if we get an IntegretyError from
    # sqlalchemy, then pass on the error.
    project = db.query(model.Project).filter_by(label = projectname).first()
    if project:
        raise DuplicateError(projectname)
    project = model.Project(projectname)
    db.add(project)
    db.commit()

def project_delete(projectname):
    """Delete project 'projectname'

    If the project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = db.query(model.Project).filter_by(label = projectname).first()
    if not project:
        raise NotFoundError(projectname)
    db.delete(project)
    db.commit()

# project takes project label
def add_group(groupname, projectname):
    """Add a project 'projectname' to an existing group
    
    If the group or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = db.query(model.Project).filter_by(label = projectname).first()
    if not project:
        raise NotFoundError(projectname)
    group = db.query(model.Group).filter_by(label = groupname).first()
    if not group:
        raise NotFoundError(groupname)
    if group.projects(project) # if project was already added to group
        raise DuplicateError(projectname)
    project.group.append(group)
    db.commit()

def remove_group(groupname, projectname):
    """Remove a project 'projectname' from an existing group
    
    If the group or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = db.query(model.Project).filter_by(label = projectname).first()
    if not project:
        raise NotFoundError(projectname)
    group = db.query(model.Group).filter_by(label = groupname).first()
    if not group:
        raise NotFoundError(groupname)
    if not group.projects(project) # if project isn't a part of the group
        raise NotFoundError(projectname)
    project.group.remove(group)
    db.commit()



                            # Node Code #
                            #############

def node_create(nodename):
    """Create node 'nodename'.

    If the node already exists, a DuplicateError will be raised.
    """
    db = model.Session()
    # XXX: This works, but we should probably have the database do the heavy
    # lifting, i.e. try to create a user, and if we get an IntegretyError from
    # sqlalchemy, then pass on the error.
    node = db.query(model.Node).filter_by(label = nodename).first()
    if node:
        raise DuplicateError(nodename)
    node = model.Node(nodename)
    db.add(node)
    db.commit()

def node_delete(nodename):
    """Delete node 'nodename'

    If the node does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    node = db.query(model.Node).filter_by(label = nodename).first()
    if not node:
        raise NotFoundError(nodename)
    db.delete(node)
    db.commit()

def add_node(nodename, projectname):
    """Add a project 'projectname' to an existing node
    
    If the node or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = db.query(model.Project).filter_by(label = projectname).first()
    if not project:
        raise NotFoundError(projectname)
    node = db.query(model.Node).filter_by(label = nodename).first()
    if not node:
        raise NotFoundError(nodename)
    if node.projects(project) # if project was already added to node
        raise DuplicateError(projectname)
    project.node.append(node)
    db.commit()

def remove_node(nodename, projectname):
    """Remove a project 'projectname' from an existing node
    
    If the node or project does not exist, a NotFoundError will be raised.
    """
    db = model.Session()
    project = db.query(model.Project).filter_by(label = projectname).first()
    if not project:
        raise NotFoundError(projectname)
    node = db.query(model.Node).filter_by(label = nodename).first()
    if not node:
        raise NotFoundError(nodename)
    if not node.projects(project) # if project isn't a part of the node
        raise NotFoundError(projectname)
    project.node.remove(node)
    db.commit()
