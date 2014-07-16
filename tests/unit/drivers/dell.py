"""Unit tests for drivers/dell.py"""

from functools import wraps

from haas import model, api
from haas.test_common import *
import pytest

from haas.config import cfg
from haas.drivers.dell import *


def dell_backend(vlan_list):
    """A decorator for tests running on the Dell backend.  Pass in a string
    for the vlan_list configuration option, which determines which vlans can
    be used for networking.
    """

    def dec(f):
        def config_initialize():
            # Use the 'dell' backend for these tests
            cfg.add_section('general')
            cfg.set('general', 'active_switch', 'dell')
            cfg.add_section('switch dell')
            cfg.set('switch dell', 'vlans', vlan_list)

        @wraps(f)
        @clear_configuration
        def wrapped(self):
            config_initialize()
            db = newDB()
            f(self, db)
            releaseDB(db)

        return wrapped

    return dec


class TestInit_DB:
    """Tests init_db."""

    @dell_backend('100-109')
    def test_init_db_1(self, db):
        pass

    @dell_backend('1-10,40-100, 4044, 3000-4000')
    def test_init_db_2(self, db):
        pass


class TestNetworkID:
    """Tests allocation and freeing of network IDs"""

    @dell_backend('84')
    def test_allocate_free_1(self, db):
        assert '84' == get_new_network_id(db)
        assert None == get_new_network_id(db)
        free_network_id(db, '84')
        assert '84' == get_new_network_id(db)
        assert None == get_new_network_id(db)

    @dell_backend('84, 85')
    def test_allocate_free_1(self, db):
        get_new_network_id(db)
        get_new_network_id(db)
        free_network_id(db, '84')
        assert '84' == get_new_network_id(db)
        free_network_id(db, '85')
        assert '85' == get_new_network_id(db)
