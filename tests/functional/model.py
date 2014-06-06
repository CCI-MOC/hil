"""Functional tests for model.py"""
from haas.model import *
from haas import config

# There's probably a better way to do this
from haas.test_common import newDB,releaseDB

class TestUsers:
    """Test user-related functionality"""

    def test_user_create_verify(self):
        db = newDB()
        user = User('bob', 'secret')
        assert user.verify_password('secret')
        releaseDB(db)
