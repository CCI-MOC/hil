from haas.model import *
import os
import tempfile
import unittest

engine = create_engine('sqlite:///:memory:', echo=True)
Base.metadata.create_all(engine)
Session.configure(bind=engine)

class ModelTest(unittest.TestCase):

    def test_user_create_verify(self):
        user = User('bob', 'secret')
        self.assertTrue(user.verify_password('secret'))
