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


class TestGroup(InsertTest):

    def test_insert(self):
        self.insert(Group('moc-hackers'))

    def test_repr(self):
        print(Group('moc-hackers'))


class TestNic(InsertTest):

    def test_insert(self):
        node = Node('node-99')
        self.insert(Nic(node, 'ipmi', '00:11:22:33:44:55'))

    def test_repr(self):
        node = Node('node-99')
        print(Nic(node, 'ipmi', '00:11:22:33:44:55'))


class TestNode(InsertTest):

    def test_insert(self):
        self.insert(Node('node-99'))

    def test_repr(self):
        print(Node('node-99'))


class TestProject(InsertTest):

    def test_insert(self):
        group = Group('acme_corp')
        self.insert(Project(group, 'manhattan'))

    def test_repr(self):
        group = Group('acme_corp')
        print(Project(group, 'node-99'))


class TestSwitch(InsertTest):

    def test_insert(self):
        self.insert(Switch('dev-switch', 'acme_corp'))

    def test_repr(self):
        print(Switch('dev-switch', 'acme-corp'))


class TestHeadnode(InsertTest):

    def test_insert(self):
        group = Group('acme_corp')
        self.insert(Headnode(group, 'hn-example'))

    def test_repr(self):
        group = Group('acme_corp')
        print(Headnode(group, 'hn-example'))


class TestHnic(InsertTest):

    def test_insert(self):
        group = Group('acme_corp')
        hn = Headnode(group, 'hn-0')
        self.insert(Hnic(group, hn, 'storage', '00:11:22:33:44:55'))

    def test_repr(self):
        group = Group('acme_corp')
        hn = Headnode(group, 'hn-0')
        print(Hnic(group, hn, 'storage', '00:11:22:33:44:55'))

class TestVlan(InsertTest):

    def test_insert(self):
        self.insert(Vlan(102))

    def test_repr(self):
        print(Vlan(102))

class TestNetwork(InsertTest):

    def test_insert(self):
        network = Network(Group('acme_corp'), Vlan(102), 'hammernet')
        self.insert(network)

    def test_repr(InsertTest):
        print(Network(Group('acme_corp'), Vlan(102), 'hammernet'))
