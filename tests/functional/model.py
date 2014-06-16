"""Functional tests for model.py"""
from haas.model import *

# There's probably a better way to do this
from haas.test_common import newDB, releaseDB


class InsertTest:
    """Superclass for tests doing basic database insertions of one object."""

    def insert(self, obj):
        db = newDB()
        db.add(obj)
        db.commit()
        releaseDB(db)


class TestUsers(InsertTest):
    """Test user-related functionality"""

    def test_user_create_verify(self):
        db = newDB()
        user = User('bob', 'secret')
        assert user.verify_password('secret')
        releaseDB(db)

    def test_user_insert(self):
        self.insert(User('bob', 'secret'))


class TestNic(InsertTest):

    def test_insert(self):
        self.insert(Nic('ipmi', '00:11:22:33:44:55'))


class TestSwitch(InsertTest):

    def test_insert(self):
        self.insert(Switch('dev-switch', 'acme_corp'))
