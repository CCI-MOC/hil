"""Functional tests for model.py"""

# Some Notes:
#
# * We don't really have any agreed-upon requirements about what __repr__
# should print, but I'm fairly certain I hit an argument mistmatch at
# some point, which is definitely wrong. The test_repr methods are there just
# to make sure it isn't throwing an exception.

from haas.model import *

# There's probably a better way to do this
from haas.test_common import newDB, releaseDB, null_config_decorator


class InsertTest:
    """Superclass for tests doing basic database insertions of one object."""

    def insert(self, db, obj):
        db.add(obj)
        db.commit()


class TestUsers(InsertTest):
    """Test user-related functionality"""

    @null_config_decorator
    def test_user_create_verify(self, db):
        user = User('bob', 'secret')
        assert user.verify_password('secret')

    @null_config_decorator
    def test_user_insert(self, db):
        self.insert(db, User('bob', 'secret'))

    def test_repr(self):
        print(User('bob', 'secret'))


class TestGroup(InsertTest):

    @null_config_decorator
    def test_insert(self, db):
        self.insert(db, Group('moc-hackers'))

    def test_repr(self):
        print(Group('moc-hackers'))


class TestNic(InsertTest):

    @null_config_decorator
    def test_insert(self, db):
        node = Node('node-99')
        self.insert(db, Nic(node, 'ipmi', '00:11:22:33:44:55'))

    def test_repr(self):
        node = Node('node-99')
        print(Nic(node, 'ipmi', '00:11:22:33:44:55'))


class TestNode(InsertTest):

    @null_config_decorator
    def test_insert(self, db):
        self.insert(db, Node('node-99'))

    def test_repr(self):
        print(Node('node-99'))


class TestProject(InsertTest):

    @null_config_decorator
    def test_insert(self, db):
        group = Group('acme_corp')
        self.insert(db, Project(group, 'manhattan'))

    def test_repr(self):
        group = Group('acme_corp')
        print(Project(group, 'node-99'))


class TestSwitch(InsertTest):

    @null_config_decorator
    def test_insert(self, db):
        self.insert(db, Switch('dev-switch', 'acme_corp'))

    def test_repr(self):
        print(Switch('dev-switch', 'acme-corp'))


class TestHeadnode(InsertTest):

    @null_config_decorator
    def test_insert(self, db):
        project = Project(Group('acme_corp'), 'anvil_nextgen')
        self.insert(db, Headnode(project, 'hn-example'))

    def test_repr(self):
        project = Project(Group('acme_corp'), 'anvil_nextgen')
        print(Headnode(project, 'hn-example'))


class TestHnic(InsertTest):

    @null_config_decorator
    def test_insert(self, db):
        project = Project(Group('acme_corp'), 'anvil_nextgen')
        hn = Headnode(project, 'hn-0')
        self.insert(db, Hnic(hn, 'storage', '00:11:22:33:44:55'))

    def test_repr(self):
        project = Project(Group('acme_corp'), 'anvil_nextgen')
        hn = Headnode(project, 'hn-0')
        print(Hnic(hn, 'storage', '00:11:22:33:44:55'))

class TestNetwork(InsertTest):

    @null_config_decorator
    def test_insert(self, db):
        project = Project(Group('acme_corp'), 'anvil_nextgen')
        network = Network(project, '34', 'hammernet')
        self.insert(db, network)

    def test_repr(InsertTest):
        project = Project(Group('acme_corp'), 'anvil_nextgen')
        print (Network(project, '34', 'hammernet'))
