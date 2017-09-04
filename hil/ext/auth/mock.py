"""Mock auth plugin for testing.

This module provides an auth backend which allows the programmer to mock
project an admin access, for use in testing. See the functions `set_project`
and `set_admin` for details.
"""
from hil import auth, rest


class MockAuthBackend(auth.AuthBackend):
    """An auth backend for mocking the request's authentication and
    authorization status.

    By default, the request does not have access to a project, and does not
    have admin access. The functions `set_admin` and `set_project` can be
    used to change this.

    If invoked before `authenticate`, `set_auth_success` may be used to change
    the return value of `authenticate`, which is useful for testing cases where
    the user is not authenticated at all. Note that if the api call functions
    are invoked directly, `authenticate` is bypassed, so you will need to
    actually spoof a full request. The defualt is True.
    """

    def __init__(self):
        self._auth_success = True

    def authenticate(self):
        # pylint: disable=missing-docstring
        rest.local.auth = {
            'project': None,
            'admin': False,
            'user': 'user',
        }
        return self._auth_success

    def get_user(self):
        """Return the user who is authenticated."""
        return rest.local.auth['user']

    def set_auth_success(self, ok):
        """Set the return value for `authenticate` to `ok`."""
        self._auth_success = ok

    def _have_admin(self):
        return rest.local.auth['admin']

    def _have_project_access(self, project):
        return project == rest.local.auth['project']

    def set_project(self, project):
        """Change the project that the request is acting on behalf of."""
        rest.local.auth['project'] = project

    def set_admin(self, admin):
        """Change whether the request has admin access.

        admin is a boolean indicating whether the request should have admin
        access.
        """
        rest.local.auth['admin'] = admin

    def set_user(self, user):
        """Set the user the request is running as."""
        rest.local.auth['user'] = user


def setup(*args, **kwargs):
    """Set a MockAuthBackend as the auth backend."""
    auth.set_auth_backend(MockAuthBackend())
