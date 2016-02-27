"""Mock auth plugin for testing.

This module provides an auth backend which allows the programmer to mock
project an admin access, for use in testing. See the functions `set_project`
and `set_admin` for details.
"""
from haas import auth, rest


class MockAuthBackend(auth.AuthBackend):
    """An auth backend for mocking the request's project and admin status.

    By default, the request does not have access to a project, and does not
    have admin access. The functions `set_admin` and `set_project` can be
    used to change this.
    """

    def authenticate(self):
        rest.local.auth = {
            'project': None,
            'admin': False,
        }
        return True

    def _have_admin(self):
        return rest.local.auth['admin']

    def _have_project_access(self, project):
        return project == rest.local.auth['project']

    def set_project(self, project):
        """Change the project that the request is acting on behalf of."""
        rest.local.auth['project'] = project

    def set_admin(self, admin):
        rest.local.auth['admin'] = admin


def setup(*args, **kwargs):
    auth.set_auth_backend(MockAuthBackend())
