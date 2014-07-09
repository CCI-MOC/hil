"""Unit tests for drivers/dell.py"""

from haas import model, api
from haas.test_common import newDB, releaseDB
import pytest

from haas.config import cfg
from haas.drivers.dell import *


def cfg_decorator(vlan_list):
    def dec(f):
        def config_initialize():
            # Use the 'dell' backend for these tests
            cfg.add_section('general')
            cfg.set('general', 'active_switch', 'dell')
            cfg.add_section('switch dell')
            cfg.set('switch dell', 'vlans', vlan_list)

        def config_clear():
            for section in cfg.sections():
                cfg.remove_section(section)

        def wrapped(self):
            config_clear()
            config_initialize()
            db = newDB()
            f(self, db)
            releaseDB(db)
            config_clear()

        wrapped.__name__ = f.__name__
        return wrapped

    return dec


class TestInit_DB:
    """Tests init_db."""

    @cfg_decorator('100-109')
    def test_init_db_1(self, db):
        pass

    @cfg_decorator('1-10,40-100, 4044, 3000-4000')
    def test_init_db_2(self, db):
        pass


class TestNetworkID:
    """Tests allocation and freeing of network IDs"""

    @cfg_decorator('84')
    def test_allocate_free_1(self, db):
        assert '84' == get_new_network_id()
        assert None == get_new_network_id()
        free_network_id('84')
        assert '84' == get_new_network_id()
        assert None == get_new_network_id()

    @cfg_decorator('84, 85')
    def test_allocate_free_1(self, db):
        get_new_network_id()
        get_new_network_id()
        free_network_id('84')
        assert '84' == get_new_network_id()
        free_network_id('85')
        assert '85' == get_new_network_id()
