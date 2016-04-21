"""'Null' auth backend

This backend requires no authentication and permits everything. Useful for
testing, do not use in production."""
from haas import auth


class NullAuthBackend(auth.AuthBackend):

    def authenticate(self):
        return True

    def get_user(self):
        return None

    def _have_admin(self):
        return True

    def _have_project_access(self, project):
        return True


def setup(*args, **kwargs):
    auth.set_auth_backend(NullAuthBackend())
