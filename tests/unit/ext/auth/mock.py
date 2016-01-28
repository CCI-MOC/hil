from haas import config, server
from haas.auth import get_auth_backend
from haas.errors import AuthorizationError
from haas.model import Project
from haas.rest import RequestContext, local
from haas.test_common import config_testsuite, config_merge, fresh_database
import pytest


@pytest.fixture
def configure():
    config_testsuite()
    config_merge({
        'extensions': {
            'haas.ext.auth.mock': '',
            'haas.ext.auth.null': None,
        },
    })
    config.load_extensions()


@pytest.fixture
def db(request):
    return fresh_database(request)


@pytest.fixture
def server_init():
    server.register_drivers()
    server.validate_state()


@pytest.yield_fixture
def with_request_context():
    with RequestContext():
        yield


@pytest.fixture
def load_projects():
    """Add a couple probjects to the database for us to work with"""
    local.db.add(Project("manhattan"))
    local.db.add(Project("runway"))


@pytest.fixture
def auth_backend():
    return get_auth_backend()


pytestmark = pytest.mark.usefixtures('configure',
                                     'db',
                                     'server_init',
                                     'with_request_context',
                                     'load_projects')


def test_default_no_admin(auth_backend):
    """By default, admin access should be denied."""
    with pytest.raises(AuthorizationError):
        auth_backend.require_admin()


def test_default_no_project(auth_backend):
    """By default, access to an arbitrary project should be denied."""
    with pytest.raises(AuthorizationError):
        auth_backend\
            .require_project_access(local.db.query(Project).first())


def test_set_admin(auth_backend):
    """Setting the admin status should affect require_admin."""
    auth_backend.set_admin(True)
    auth_backend.require_admin()
    auth_backend.set_admin(False)
    with pytest.raises(AuthorizationError):
        auth_backend.require_admin()


def test_set_project_access(auth_backend):
    """Setting the project should affect require_project_access."""
    runway = local.db.query(Project).filter_by(label="runway").one()
    manhattan = local.db.query(Project).filter_by(label="manhattan").one()
    auth_backend.set_project(runway)
    auth_backend.require_project_access(runway)
    auth_backend.set_project(manhattan)
    auth_backend.require_project_access(manhattan)
    with pytest.raises(AuthorizationError):
        auth_backend.require_project_access(runway)


def test_admin_implies_project_access(auth_backend):
    """Admin access implies access to any project."""
    runway = local.db.query(Project).filter_by(label="runway").one()
    manhattan = local.db.query(Project).filter_by(label="manhattan").one()
    auth_backend.set_admin(True)
    auth_backend.require_project_access(runway)
    auth_backend.require_project_access(manhattan)
