"""Keystone authentication backend.

This is a thin wrapper around the `keystonemiddleware` library.
"""
from keystonemiddleware.auth_token import filter_factory
from flask import request
from hil.flaskapp import app
from hil.config import cfg
from hil.model import Project
from hil import auth, rest
import logging
import sys

logger = rest.ContextLogger(logging.getLogger(__name__), {})


class KeystoneAuthBackend(auth.AuthBackend):
    """Authenticate with keystone."""

    def authenticate(self):
        # pylint: disable=missing-docstring

        # keystonemiddleware makes auth info available from two places:
        #
        # 1. Variables in the wsgi environment
        # 2. Extra HTTP headers.
        #
        # In general, the wsgi variable 'HTTP_FOO_BAR' is equivalent to the
        # HTTP header 'Foo-Bar'.
        #
        # We use the wsgi environment's variables below; it shouldn't matter,
        # but this way if something goes horribly wrong and arbitrary headers
        # aren't stripped out, the client can't just inject these.
        if request.environ['HTTP_X_IDENTITY_STATUS'] != 'Confirmed':
            return False

        if self._have_admin():
            return True

        project_id = request.environ['HTTP_X_PROJECT_ID']
        if Project.query.filter_by(label=project_id).first() is None:
            logger.info("Successful authentication by Openstack project %r, "
                        "but this project is not registered with HIL",
                        project_id)
            return False

        return True

    def _have_project_access(self, project):
        return project.label == request.environ['HTTP_X_PROJECT_ID']

    def _have_admin(self):
        return 'admin' in request.environ['HTTP_X_ROLES'].split(',')


def setup(*args, **kwargs):
    """Set a KeystoneAuthBackend as the auth backend.

    Loads keystone settings from hil.cfg.
    """
    if not cfg.has_section(__name__):
        logger.error('No section for [%s] in hil.cfg; authentication will '
                     'not work without this. Please add this section and try '
                     'again.', __name__)
        sys.exit(1)
    keystone_cfg = {}
    for key in cfg.options(__name__):
        keystone_cfg[key] = cfg.get(__name__, key)

    # Great job with the API design Openstack! </sarcasm>
    factory = filter_factory(keystone_cfg)
    app.wsgi_app = factory(app.wsgi_app)

    auth.set_auth_backend(KeystoneAuthBackend())
