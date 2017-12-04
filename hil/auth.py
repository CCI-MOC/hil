"""Authentication and authorization."""

from hil.errors import AuthorizationError
from hil import model
from abc import ABCMeta, abstractmethod

import sys

_auth_backend = None


class AuthBackend(object):
    """An authentication/authorization backend.

    Extensions which implement authentication/authorization backends should
    inherit from this class, and invoke ``set_auth_backend()`` on an instance
    of the subclass

    Subclasses of AuthBackend must override `authenticate`, `_have_admin`,
    and `_have_project_access`, and nothing else. Users of the AuthBackend must
    not invoke `_have_admin` and `_have_project_access`, preferring
    `have_admin` and `have_project_access`.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def authenticate(self):
        """Authenticate the api call, and prepare for later authorization checks.

        This method will be invoked inside of a flask request context,
        with ``hil.rest.local.db`` initialized to a valid database session.
        It is responsible for authenticating the request, and storing any
        data it will need later to determine whether the requested operation
        is authorized.

        The attribute ``hil.rest.local.auth`` is reserved for use by auth
        backends; A backend may store any information it needs as that
        attribute.

        This method must return a boolean indicating whether or not
        authentication was successful -- True if so, False if not.
        """
        # FIXME: for some reason I(zenhack) don't understand, pylint doesn't
        # pick up on this being an abstract method, and still gives warnings
        # about missing docstrings on implementations. For now, we just
        # locally disable the warnings in those places, but we ought to figure
        # out what's going on.

    @abstractmethod
    def _have_admin(self):
        """Check if the request is authorized to act as an administrator.

        Return True if so, False if not. This will be called sometime after
        ``authenticate()``.
        """

    @abstractmethod
    def _have_project_access(self, project):
        """Check if the request is authorized to act as the given project.

        Each backend must implement this method. The backend does not need
        to deal with the case where the authenticated user is an admin here;
        the `have_*` and `require_*` wrappers handle this.
        """

    def have_admin(self):
        """Check if the request is authorized to act as an administrator.

        Return True if so, False if not. This will be caled sometime after
        ``authenticate()``.
        """
        return self._have_admin()

    def have_project_access(self, project):
        """Check if the request is authorized to act as the given project.

        Return True if so, False if not. This will be caled sometime after
        ``authenticate()``.

        Note that have_admin implies have_project_acccess.

        ``project`` will be a ``Project`` object, *not* the name of the
        project. It may also be ``None``, in which case this is equivalent
        to ``have_admin``.
        """

        if project is None:
            return self._have_admin()

        assert isinstance(project, model.Project)
        return self._have_admin() or self._have_project_access(project)

    def require_admin(self):
        """Ensure the request is authorized to act as an administrator.

        Raises an ``AuthorizationError`` on failure, instead of returning
        False. This is a convienence wrapper around ``have_admin``,
        and should not be overwritten by subclasses.
        """
        if not self.have_admin():
            raise AuthorizationError("This operation is administrator-only.")

    def require_project_access(self, project):
        """Like ``require_admin()``, but wraps ``have_project_access()``."""
        if not self.have_project_access(project):
            raise AuthorizationError(
                "You do not have access to the required project.")


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
