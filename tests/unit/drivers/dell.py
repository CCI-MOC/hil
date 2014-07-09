"""Unit tests for drivers/dell.py"""

from haas import model, api
from haas.test_common import newDB, releaseDB
import pytest

from haas.config import cfg

from haas.drivers.dell import *

# Use the 'dell' backend for these tests
cfg.add_section('general')
cfg.set('general', 'active_switch', 'dell')

cfg.add_section('switch dell')

class TestInit_DB:
    """Tests init_db."""

    def test_init_db_1(self):
        cfg.set('switch dell', 'vlans', '100-109')
        db = newDB()
        releaseDB(db)

    def test_init_db_2(self):
        cfg.set('switch dell', 'vlans', '1-10,40-100, 9004, 3000-4000')
        db = newDB()
        releaseDB(db)

class TestNetworkID:
    """Tests allocation and freeing of network IDs"""

    def test_allocate_free_1(self):
        cfg.set('switch dell', 'vlans', '84')
        db = newDB()
        assert '84' == get_new_network_id()
        assert None == get_new_network_id()
        free_network_id('84')
        assert '84' == get_new_network_id()
        assert None == get_new_network_id()
        releaseDB(db)

    def test_allocate_free_1(self):
        cfg.set('switch dell', 'vlans', '84, 85')
        db = newDB()
        get_new_network_id()
        get_new_network_id()
        free_network_id('84')
        assert '84' == get_new_network_id()
        free_network_id('85')
        assert '85' == get_new_network_id()
        releaseDB(db)
