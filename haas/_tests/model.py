from haas.model import *
from haas import config
import os
import tempfile
import unittest

class ModelTest(unittest.TestCase):
    """A base class for our model test cases.

    Right now this just abstracts away the logic to set up a new database.
    """
    def setUp(self):
        tmp = tempfile.mkdtemp()
        os.chdir(tmp)
        with open('haas.cfg', 'w') as f:
            f.write("""
[database]
uri = sqlite:///:memory:
""")
        config.load()
        init_db(create=True)

class ModelInsertTest(ModelTest):
    """A base class for testing insertion of objects into the database."""

    def insert(self, obj):
        """Attempts to insert the object into the database."""
        db = Session()
        db.add(obj)
        db.commit()


class NicInsertTest(ModelInsertTest):

    def test_insert(self):
        nic = Nic('ipmi', '00:11:22:33:44:55')
        self.insert(nic)


class UserInsertTest(ModelInsertTest):

    def test_insert(self):
        user = User('bob', 'secret')
        self.insert(user)


class SwitchInsertTest(ModelInsertTest):

    def test_insert(self):
        sw = Switch('dev-switch', 'acme_corp')
        self.insert(sw)


class UserMethodTest(ModelTest):
    """Tests the User class's logic which is independent from the database. """

    def test_user_create_verify(self):
        """Basic test of password verification."""

        user = User('bob', 'secret')
        self.assertTrue(user.verify_password('secret'))
