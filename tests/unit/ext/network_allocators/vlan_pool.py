from haas.test_common import config_testsuite, config_merge, \
    fresh_database
from haas.config import load_extensions
from haas.flaskapp import app
from haas.model import db
from haas.migrations import create_db
from haas.ext.network_allocators.vlan_pool import Vlan
import pytest


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
