
import unittest

import os
import tempfile

# XXX: ick. this is necessary because the model module creates/opens the
# database upon import. see issue #10.
tmpdir = tempfile.mkdtemp()
os.chdir(tmpdir)
from haas import model
from haas.model import session

from haas.control import *

class TestModels(unittest.TestCase):
    
    def test_create_vlans(self):
        create_vlan(104)
        create_vlan(105)
        self.assertEqual(len(session.query(model.Vlan).all()), 2)

    # This is failing right now, as create_vlan is throwing an
    # exception. The test isn't finished yet; we want to check that
    # create_vlan is throwing a semantically meaningful exception,
    # rather than the one passed up from sqlalchemy.
    def test_duplicate(self):
        create_vlan(108)
        create_vlan(108)


if __name__ == '__main__':
    unittest.main()
