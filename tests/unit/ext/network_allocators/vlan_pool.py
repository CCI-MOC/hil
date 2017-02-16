from haas.config import load_extensions
from haas.flaskapp import app
from haas.model import db
from haas.migrations import create_db
from haas import api, model, server
from haas.test_common import *
import pytest

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)
with_request_context = pytest.yield_fixture(with_request_context)
fresh_database = pytest.fixture(fresh_database)


@pytest.fixture
def server_init():
    server.register_drivers()
    server.validate_state()


@pytest.fixture
def configure():
    config_testsuite()
    config_merge({
        'extensions': {
            'haas.ext.network_allocators.null': None,
            'haas.ext.network_allocators.vlan_pool': ''
        },
        'haas.ext.network_allocators.vlan_pool': {
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
    from haas.ext.network_allocators.vlan_pool import Vlan
    with app.app_context():
        # flag vlan 100 as in-use, just so the db isn't quite pristine.
        vlan100 = Vlan.query.filter_by(vlan_no=100)
        vlan100.available = False
        db.session.commit()
    # Okay, now try re-initializing:
    create_db()


def test_vlanid_for_admin_network():
    """
    Test for valid vlanID for administrator-owned networks.
    """
    # create a network with a string vlan id
    with pytest.raises(api.BadArgumentError):
        api.network_create('hammernet', 'admin', '', 'yes')

    # create a network with a vlanid>4096
    with pytest.raises(api.BadArgumentError):
        api.network_create('nailnet', 'admin', '', '5023')

    # create a netowrk with a vlanid<1
    with pytest.raises(api.BadArgumentError):
        api.network_create('nailnet', 'admin', '', '-2')
