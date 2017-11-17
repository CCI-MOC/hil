"""Tests related to the maintenance pool."""
from hil import model, config, api
from hil.test_common import config_testsuite, config_merge, fresh_database, \
    fail_on_log_warnings, additional_db, with_request_context, \
    server_init, LoggedWarningError
from hil.auth import get_auth_backend
import pytest

OBM_TYPE_MOCK = 'http://schema.massopencloud.org/haas/v0/obm/mock'


@pytest.fixture
def configure():
    """Configure HIL"""
    config_testsuite()
    config_merge({
        'auth': {
            'require_authentication': 'False',
        },
        'extensions': {
            'hil.ext.auth.null': None,
            'hil.ext.auth.mock': '',
            'hil.ext.switches.mock': '',
            'hil.ext.obm.ipmi': '',
            'hil.ext.obm.mock': '',
            'hil.ext.network_allocators.null': None,
            'hil.ext.network_allocators.vlan_pool': '',
        },
        'hil.ext.network_allocators.vlan_pool': {
            'vlans': '40-80',
        },
        'maintenance': {
            'maintenance_project': 'maintenance',
            # Keystone url acts as dummy for posting
            'url': 'http://127.0.0.1:9999/test/'
        }
    })
    config.load_extensions()


fresh_database = pytest.fixture(fresh_database)
additional_database = pytest.fixture(additional_db)
fail_on_log_warnings = pytest.fixture(fail_on_log_warnings)
server_init = pytest.fixture(server_init)


with_request_context = pytest.yield_fixture(with_request_context)


@pytest.fixture
def set_admin_auth():
    """Set admin auth for all calls"""
    get_auth_backend().set_admin(True)


@pytest.fixture
def maintenance_proj_init():
    """Create maintenance project."""
    api.project_create('maintenance')


def new_node(name):
    """Create a mock node named ``name``"""
    api.node_register(name, obm={
              "type": OBM_TYPE_MOCK,
              "host": "ipmihost",
              "user": "root",
              "password": "tapeworm"})


default_fixtures = ['fail_on_log_warnings',
                    'configure',
                    'fresh_database',
                    'server_init',
                    'with_request_context',
                    'set_admin_auth']

pytestmark = pytest.mark.usefixtures(*default_fixtures)


class TestProjectDetachNodeMaintenance:
    """Test project_detach_node with maintenance pool enabled.
    The main point of this test is to ensure that the node goes
    into the maintenance pool if it is not already, and that the
    POST request is successfully detected with an intentional error."""

    def test_project_detach_node_maintenance(self, maintenance_proj_init):
        """Test that project_detach_node removes the node from the project.
        Note that the maintenance server has a fake url.  We expect it to
        fail during the connection."""
        api.project_create('anvil-nextgen')
        new_node('node-99')
        api.project_connect_node('anvil-nextgen', 'node-99')
        # Should raise error due to arbitrary POST url:
        with pytest.raises(LoggedWarningError):
            api.project_detach_node('anvil-nextgen', 'node-99')
        maintenance_proj = api._must_find(model.Project, 'maintenance')
        node = api._must_find(model.Node, 'node-99')
        assert node.project == maintenance_proj
