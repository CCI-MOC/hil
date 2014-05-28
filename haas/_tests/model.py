from haas.model import *
from haas import config
import os
import tempfile
import unittest

class ModelTest(unittest.TestCase):

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

    def test_user_create_verify(self):
        user = User('bob', 'secret')
        self.assertTrue(user.verify_password('secret'))
