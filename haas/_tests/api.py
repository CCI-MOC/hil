from haas import model, config, api

import os
import tempfile
import unittest

class user_create_Test(unittest.TestCase):
    """Tests for the haas.api.user_create function."""

    def setUp(self):
        tmp = tempfile.mkdtemp()
        os.chdir(tmp)
        with open('haas.cfg', 'w') as f:
            f.write('[database]\n')
            f.write('uri = sqlite:///:memory:\n')
        config.load()
        model.init_db(create=True)

    def test_00_new_user_should_succeed(self):
        api._assert_absent(model.Session(), model.User, 'bob')
        api.user_create('bob', 'foo')

    def test_01_duplicate_user_should_fail(self):
        api.user_create('alice', 'secret')
        self.assertRaises(api.DuplicateError,
                api.user_create, 'alice', 'password')

