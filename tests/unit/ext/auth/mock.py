"""Test the mock auth backend"""
from hil import config
from hil.auth import get_auth_backend
from hil.errors import AuthorizationError
from hil.model import db, Project
from hil.test_common import config_testsuite, config_merge, fresh_database, \
    with_request_context, fail_on_log_warnings, server_init
import pytest


@pytest.fixture
def configure():
    """Configure HIL"""
    config_testsuite()
    config_merge({
        'extensions': {
            'hil.ext.auth.mock': '',
            'hil.ext.auth.null': None,
        },
    })
    config.load_extensions()


fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)
fresh_database = pytest.fixture(fresh_database)
server_init = pytest.fixture(server_init)
with_request_context = pytest.yield_fixture(with_request_context)


@pytest.fixture
def load_projects():
    """Add a couple probjects to the database for us to work with"""
    db.session.add(Project("manhattan"))
    db.session.add(Project("runway"))


@pytest.fixture
def auth_backend():
    """Fixture returning the auth backend"""
    return get_auth_backend()


pytestmark = pytest.mark.usefixtures('configure',
                                     'fresh_database',
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
            .require_project_access(Project.query.first())


def test_set_admin(auth_backend):
    """Setting the admin status should affect require_admin."""
    auth_backend.set_admin(True)
    auth_backend.require_admin()
    auth_backend.set_admin(False)
    with pytest.raises(AuthorizationError):
        auth_backend.require_admin()


def test_set_project_access(auth_backend):
    """Setting the project should affect require_project_access."""
    runway = Project.query.filter_by(label="runway").one()
    manhattan = Project.query.filter_by(label="manhattan").one()
    auth_backend.set_project(runway)
    auth_backend.require_project_access(runway)
    auth_backend.set_project(manhattan)
    auth_backend.require_project_access(manhattan)
    with pytest.raises(AuthorizationError):
        auth_backend.require_project_access(runway)


def test_admin_implies_project_access(auth_backend):
    """Admin access implies access to any project."""
    runway = Project.query.filter_by(label="runway").one()
    manhattan = Project.query.filter_by(label="manhattan").one()
    auth_backend.set_admin(True)
    auth_backend.require_project_access(runway)
    auth_backend.require_project_access(manhattan)
