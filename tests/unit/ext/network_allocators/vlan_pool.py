"""Test the vlan_pool network allocator."""
from hil.config import load_extensions
from hil.flaskapp import app
from hil.model import db
from hil.migrations import create_db
from hil import api, errors
from hil.test_common import fail_on_log_warnings, with_request_context, \
    fresh_database, config_testsuite, config_merge, server_init
from hil import model
import pytest

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)
with_request_context = pytest.yield_fixture(with_request_context)
fresh_database = pytest.fixture(fresh_database)
server_init = pytest.fixture(server_init)


@pytest.fixture
def configure():
    """Configure HIL"""
    config_testsuite()
    config_merge({
        'extensions': {
            'hil.ext.network_allocators.null': None,
            'hil.ext.network_allocators.vlan_pool': ''
        },
        'hil.ext.network_allocators.vlan_pool': {
            'vlans': '100-104, 300, 702',  # Arbitrary list
        },
    })
    load_extensions()


default_fixtures = ['fail_on_log_warnings',
                    'configure',
                    'fresh_database',
                    'server_init',
                    'with_request_context']

pytestmark = pytest.mark.usefixtures(*default_fixtures)


def test_populate_dirty_db():
    """running the allocator's populate() on an existing db should be ok.

    This includes the case where modifications have been made to the vlans
    in the database.

    Note that we only check that this doesn't raise an exception.
    """
    # The fresh_database fixture will have created a clean database for us. We
    # just tweak it and then re-run create_db
    from hil.ext.network_allocators.vlan_pool import Vlan
    with app.app_context():
        # flag vlan 100 as in-use, just so the db isn't quite pristine.
        vlan100 = Vlan.query.filter_by(vlan_no=100).one()
        vlan100.available = False
        db.session.commit()
    # Okay, now try re-initializing:
    create_db()


def test_vlanid_for_admin_network():
    """
    Test for valid vlanID for administrator-owned networks.
    """
    # create a network with a string vlan id
    with pytest.raises(errors.BadArgumentError):
        api.network_create('hammernet', 'admin', '', 'yes')

    # create a network with a vlanid>4096
    with pytest.raises(errors.BadArgumentError):
        api.network_create('nailnet', 'admin', '', '5023')

    # create a netowrk with a vlanid<1
    with pytest.raises(errors.BadArgumentError):
        api.network_create('nailnet', 'admin', '', '-2')


class TestAdminCreatedNetworks():
    """
    Test networks created by administrator
    """

    def test_create_network_with_id_from_pool(self):
        """Test creation of networks with IDs from the pool."""

        api.project_create('nuggets')

        # create a project owned network and get its network_id
        api.network_create('hammernet', 'nuggets', 'nuggets', '')
        network = api._must_find(model.Network, 'hammernet')
        net_id = int(network.network_id)
        assert network.allocated is True

        # create an admin owned network with net_id from pool
        api.network_create('nailnet', 'admin', '', 103)
        network = api._must_find(model.Network, 'nailnet')
        assert network.allocated is True

        # creating a network with the same network id should raise an error
        with pytest.raises(errors.BlockedError):
            api.network_create('redbone', 'admin', '', 103)
        with pytest.raises(errors.BlockedError):
            api.network_create('starfish', 'admin', '', net_id)

        # free the network ids by deleting the networks
        api.network_delete('hammernet')
        api.network_delete('nailnet')
        api._assert_absent(model.Network, 'hammernet')
        api._assert_absent(model.Network, 'nailnet')

        # after deletion we should be able to create admin networks with those
        # network_ids
        api.network_create('redbone', 'admin', '', 103)
        network = api._must_find(model.Network, 'redbone')
        assert int(network.network_id) == 103

        api.network_create('starfish', 'admin', '', net_id)
        network = api._must_find(model.Network, 'starfish')
        assert int(network.network_id) == net_id

    def test_create_network_with_id_outside_pool(self):
        """Test creation of networks whose ID is not in the pool."""

        # create an admin owned network
        api.network_create('hammernet', 'admin', '', 1511)

        # administrators should be able to make different networks with the
        # same network id

        api.network_create('starfish', 'admin', '', 1511)
        network = api._must_find(model.Network, 'starfish')
        net_id = int(network.network_id)
        assert network.allocated is False
        assert net_id == 1511
