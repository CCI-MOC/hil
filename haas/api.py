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
