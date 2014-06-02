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

class UserMethodTest(ModelTest):
    """Tests the User class's logic which is independent from the database. """

    def test_user_create_verify(self):
        """Basic test of password verification."""

        user = User('bob', 'secret')
        self.assertTrue(user.verify_password('secret'))
