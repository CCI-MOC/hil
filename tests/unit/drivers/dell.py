"""Unit tests for drivers/dell.py"""

from haas import model, api
from haas.test_common import newDB, releaseDB
import pytest

from haas.config import cfg

# Use the 'dell' backend for these tests
cfg.add_section('general')
cfg.set('general', 'active_switch', 'dell')

cfg.add_section('switch dell')

class TestInit_DB:
    """Tests init_db."""

    def test_init_db_1(self):
        db = newDB()
        releaseDB(db)
