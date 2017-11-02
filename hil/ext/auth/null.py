"""'Null' auth backend

This backend requires no authentication and permits everything. Useful for
testing, do not use in production."""
from hil import auth

import logging
from hil.rest import ContextLogger

logger = ContextLogger(logging.getLogger(__name__), {})


class NullAuthBackend(auth.AuthBackend):
    """A null authentication backend.

    Authentication always succeeds, giving admin access.
    """

    def authenticate(self):
        # pylint: disable=missing-docstring
        logger.info("successful authentication with null backend.")
        return True

    def _have_admin(self):
        return True

    def _have_project_access(self, project):
        return True


def setup(*args, **kwargs):
    """Set a NullAuthBackend as the auth backend."""
    auth.set_auth_backend(NullAuthBackend())
