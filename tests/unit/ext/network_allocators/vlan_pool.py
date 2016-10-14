from haas.test_common import config_testsuite, config_merge, \
    fresh_database, fail_on_log_warnings
from haas.config import load_extensions
from haas.flaskapp import app
from haas.model import db
from haas.migrations import create_db
from haas.ext.network_allocators.vlan_pool import Vlan
from haas import api, model
import pytest

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


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

fresh_database = pytest.fixture(fresh_database)

pytestmark = pytest.mark.usefixtures('configure',
                                     'fresh_database',
                                     )
default_fixtures = ['fail_on_log_warnings',
                    'configure',
                    'fresh_database',
                    'server_init',
                    'with_request_context']


def test_populate_dirty_db():
    """running the allocator's populate() on an existing db should be ok.

    This includes the case where modifications have been made to the vlans
    in the database.

    Note that we only check that this doesn't raise an exception.
    """
    # The fresh_database fixture will have created a clean database for us. We
    # just tweak it and then re-run create_db
    with app.app_context():
        # flag vlan 100 as in-use, just so the db isn't quite pristine.
        vlan100 = Vlan.query.filter_by(vlan_no=100)
        vlan100.available = False
        db.session.commit()
    # Okay, now try re-initializing:
    create_db()


def test_test():
    """test test to see if something is up with postgresql
    """
    with pytest.raises(api.BadArgumentError):
        api.network_create('hammernet', 'admin', '', 'yes')


# def test_vlanid_for_admin_network():
#     """
#     Test for valid vlanID for administrator-owned networks.
#     """
#     # create a network with a string vlan id
#     with pytest.raises(api.BadArgumentError):
#         api.network_create('hammernet', 'admin', '', 'yes')

#     # create a network with a vlanid>4096
#     with pytest.raises(api.BadArgumentError):
#         api.network_create('nailnet', 'admin', '', '5023')

#     # create a netowrk with a vlanid<1
#     with pytest.raises(api.BadArgumentError):
#         api.network_create('nailnet', 'admin', '', '-2')
