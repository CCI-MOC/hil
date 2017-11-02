"""Auth plugin using usernames & passwords in the DB, with HTTP basic auth.

Includes API calls for managing users.
"""
from hil import api, model, auth, errors
from hil.model import db
from hil.auth import get_auth_backend
from hil.rest import rest_call, local, ContextLogger
from passlib.hash import sha512_crypt
from schema import Schema, Optional
import flask
import logging
from os.path import join, dirname
from hil.migrations import paths
from hil.model import BigIntegerType

logger = ContextLogger(logging.getLogger(__name__), {})

paths[__name__] = join(dirname(__file__), 'migrations', 'database')


class User(db.Model):
    """A user of the HIL.

    A user can be a member of any number of projects, which grants them access
    to that process's resources. A user may also be flagged as an administrator
    """
    id = db.Column(BigIntegerType, primary_key=True)
    label = db.Column(db.String, nullable=False)

    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    # The user's salted & hashed password. We currently use sha512 as the
    # hashing algorithm:
    hashed_password = db.Column(db.String)

    # The projects of which the user is a member.
    projects = db.relationship('Project',
                               secondary='user_projects',
                               backref='users')

    def __init__(self, label, password, is_admin=False):
        """Create a user `label` with the specified (plaintext) password."""
        self.label = label
        self.is_admin = is_admin
        self.set_password(password)

    def verify_password(self, password):
        """Return whether `password` is the user's (plaintext) password."""
        return sha512_crypt.verify(password, self.hashed_password)

    def set_password(self, password):
        """Set the user's password to `password` (which must be plaintext)."""
        self.hashed_password = sha512_crypt.encrypt(password)


# A joining table for users and projects, which have a many to many
# relationship:
user_projects = db.Table('user_projects',
                         db.Column('user_id', db.ForeignKey('user.id')),
                         db.Column('project_id', db.ForeignKey('project.id')))


@rest_call('PUT', '/auth/basic/user/<user>', schema=Schema({
    'user': basestring,
    'password': basestring,
    Optional('is_admin'): bool,
}), dont_log=('password',))
def user_create(user, password, is_admin=False):
    """Create user with given password.

    If the user already exists, a DuplicateError will be raised.
    """
    get_auth_backend().require_admin()

    # XXX: We need to do a bit of refactoring, so this is available outside of
    # hil.api:
    api._assert_absent(User, user)

    user = User(user, password, is_admin=is_admin)
    db.session.add(user)
    db.session.commit()


@rest_call('DELETE', '/auth/basic/user/<user>', Schema({'user': basestring}))
def user_delete(user):
    """Delete user.

    If the user does not exist, a NotFoundError will be raised.
    """
    get_auth_backend().require_admin()

    # XXX: We need to do a bit of refactoring, so this is available outside of
    # hil.api:
    user = api._must_find(User, user)

    db.session.delete(user)
    db.session.commit()


@rest_call('POST', '/auth/basic/user/<user>/add_project', Schema({
    'user': basestring,
    'project': basestring,
}))
def user_add_project(user, project):
    """Add a user to a project.

    If the project or user does not exist, a NotFoundError will be raised.
    """
    get_auth_backend().require_admin()
    user = api._must_find(User, user)
    project = api._must_find(model.Project, project)
    if project in user.projects:
        raise errors.DuplicateError(
            'User %s is already in project %s' % (user.label, project.label))
    user.projects.append(project)
    db.session.commit()


@rest_call('POST', '/auth/basic/user/<user>/remove_project', Schema({
    'user': basestring,
    'project': basestring,
}))
def user_remove_project(user, project):
    """Remove a user from a project.

    If the project or user does not exist, a NotFoundError will be raised.
    """
    get_auth_backend().require_admin()
    user = api._must_find(User, user)
    project = api._must_find(model.Project, project)
    if project not in user.projects:
        raise errors.NotFoundError(
            "User %s is not in project %s" % (user.label, project.label))
    user.projects.remove(project)
    db.session.commit()


@rest_call('PATCH', '/auth/basic/user/<user>', Schema({
    'user': basestring,
    'is_admin': bool,
}))
def user_set_admin(user, is_admin):
    """Set whether the user is an admin."""
    get_auth_backend().require_admin()
    user = api._must_find(User, user)
    if user.label == local.auth.label:
        raise errors.IllegalStateError("Cannot set own admin status")
    user.is_admin = is_admin
    db.session.commit()


class DatabaseAuthBackend(auth.AuthBackend):
    """
    Auth backend using basic auth, with usernames & passwords stored in the DB.
    """

    def authenticate(self):
        # pylint: disable=missing-docstring
        local.auth = None
        if flask.request.authorization is None:
            return False
        authorization = flask.request.authorization
        if authorization.password is None:
            return False

        user = api._must_find(User, authorization.username)
        if user.verify_password(authorization.password):
            local.auth = user
            logger.info("Successful authentication for user %r", user.label)
            return True
        else:
            logger.info("Failed authentication for user %r", user.label)
            return False

    def _have_admin(self):
        user = local.auth
        return user is not None and user.is_admin

    def _have_project_access(self, project):
        user = local.auth
        return user is not None and project in user.projects


def setup(*args, **kwargs):
    """Set a DatabaseAuthBackend as the auth backend."""
    auth.set_auth_backend(DatabaseAuthBackend())
