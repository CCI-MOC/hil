"""Tests related to the maintenance pool."""
from hil import model, config, api
from hil.test_common import config_testsuite, config_merge, fresh_database, \
    fail_on_log_warnings, additional_db, with_request_context, \
    server_init, LoggedWarningError
from hil.auth import get_auth_backend
import pytest

MOCK_SWITCH_TYPE = 'http://schema.massopencloud.org/haas/v0/switches/mock'
OBM_TYPE_MOCK = 'http://schema.massopencloud.org/haas/v0/obm/mock'
OBM_TYPE_IPMI = 'http://schema.massopencloud.org/haas/v0/obm/ipmi'
PORTS = ['gi1/0/1', 'gi1/0/2', 'gi1/0/3', 'gi1/0/4', 'gi1/0/5']


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
            'url': 'http://localhost/foo/bar'
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
def switchinit():
    """Create a switch with one port"""
    api.switch_register('sw0',
                        type=MOCK_SWITCH_TYPE,
                        username="switch_user",
                        password="switch_pass",
                        hostname="switchname")
    api.switch_register_port('sw0', PORTS[2])


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
    """Test project_detach_node."""

    def test_project_detach_node_maintenance(self, maintenance_proj_init):
        """Test that project_detach_node removes the node from the project.
        Note that the maintenance server has a fake url.  We expect it to
        fail during the connection."""
        api.project_create('anvil-nextgen')
        new_node('node-99')
        api.project_connect_node('anvil-nextgen', 'node-99')
        with pytest.raises(LoggedWarningError):
            api.project_detach_node('anvil-nextgen', 'node-99')
        project = api._must_find(model.Project, 'anvil-nextgen')
        maintenance_proj = api._must_find(model.Project, 'maintenance')
        node = api._must_find(model.Node, 'node-99')
        assert node not in project.nodes
        assert node.project is not project
        assert node.project is maintenance_proj
