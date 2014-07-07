"""Functional tests for model.py"""

# Some Notes:
#
# * We don't really have any agreed-upon requirements about what __repr__
# should print, but I'm fairly certain I hit an argument mistmatch at
# some point, which is definitely wrong. The test_repr methods are there just
# to make sure it isn't throwing an exception.

from haas.model import *

# There's probably a better way to do this
from haas.test_common import newDB, releaseDB

class ModelTest:
    """Superclass with tests common to all models."""

    def test_repr(self):
        print(self.sample_obj())

    def test_insert(self):
        db = newDB()
        db.add(self.sample_obj())
        db.commit()
        releaseDB(db)


class TestUsers(ModelTest):
    """Test user-related functionality"""

    def sample_obj(self):
        return User('bob', 'secret')

    def test_user_create_verify(self):
        db = newDB()
        user = User('bob', 'secret')
        assert user.verify_password('secret')
        releaseDB(db)


class TestGroup(ModelTest):

    def sample_obj(self):
        return Group('moc-hackers')


class TestNic(ModelTest):

    def sample_obj(self):
        node = Node('node-99')
        return Nic(node, 'ipmi', '00:11:22:33:44:55')


class TestNode(ModelTest):

    def sample_obj(self):
        return Node('node-99')


class TestProject(ModelTest):

    def sample_obj(self):
        group = Group('acme_corp')
        return Project(group, 'manhattan')


class TestSwitch(ModelTest):

    def sample_obj(self):
        return Switch('dev-switch', 'acme_corp')


class TestHeadnode(ModelTest):

    def sample_obj(self):
        group = Group('acme_corp')
        return Headnode(group, 'hn-example')


class TestHnic(ModelTest):

    def sample_obj(self):
        group = Group('acme_corp')
        hn = Headnode(group, 'hn-0')
        return Hnic(group, hn, 'storage', '00:11:22:33:44:55')


class TestVlan(ModelTest):

    def sample_obj(self):
        return Vlan(102)


class TestNetwork(ModelTest):

    def sample_obj(self):
        return Network(Group('acme_corp'), Vlan(102), 'hammernet')
