"""Authentication and authorization."""

from haas.errors import AuthorizationError
from abc import ABCMeta, abstractmethod

import sys

_auth_backend = None


class AuthBackend(object):
    """An authentication/authorization backend.

    Extensions which implement authentication/authorization backends should
    inherit from this class, and invoke ``set_auth_backend()`` on an instance
    of the subclass
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def authenticate(self):
        """Authenticate the api call, and prepare for later authorization checks.

        This method will be invoked inside of a request context, meaning
        ``haas.rest.local.request`` will be available. It is responsible for
        authenticating the request, and storing any data it will need later to
        determine whether the requested operation is authorized.

        The attribute ``haas.rest.local.auth`` is reserved for use by auth
        backends; A backend may store any information it needs as that
        attribute.
        """

    @abstractmethod
    def have_admin(self):
        """Check if the request is authorized to act as an administrator.

        Return True if so, False if not. This will be caled sometime after
        ``authenticate()``.
        """

    @abstractmethod
    def have_project_access(self, project):
        """Check if the request is authorized to act as the given project.

        Return True if so, False if not. This will be caled sometime after
        ``authenticate()``.

        ``project`` will be a ``Project`` object, *not* the name of the
        project.
        """

    def require_admin(self):
        """Ensure the request is authorized to act as an administrator.

        Raises an ``AuthorizationError`` on failure, instead of returning False.
        This is a convienence wrapper around ``have_admin``, and should not be
        overwritten by subclasses.
        """
        if not self.have_admin():
            raise AuthorizationError("This operation is administrator-only.")

    def require_project_access(self, project):
        """Like ``require_admin()``, but wraps ``have_project_access()``."""
        if not self.have_project_access(project):
            raise AuthorizationError("You do not have access to the required project.")


def set_auth_backend(backend):
    """Set the authentication backend to ``backend``.

    This should be called exactly once, on startup, with an instance of
    ``AuthBackend`` as it's argument.
    """
    global _auth_backend
    if _auth_backend is not None:
        sys.exit("Fatal Error: set_auth_backed() called twice. Make sure "
                 "you don't have conflicting extensions loaded.")
    _auth_backend = backend


def get_auth_backend():
    """Return the current auth backend."""
    return _auth_backend
