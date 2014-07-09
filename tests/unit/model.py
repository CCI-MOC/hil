"""Functional tests for model.py"""

# Some Notes:
#
# * We don't really have any agreed-upon requirements about what __repr__
# should print, but I'm fairly certain I hit an argument mistmatch at
# some point, which is definitely wrong. The test_repr methods are there just
# to make sure it isn't throwing an exception.

from abc import ABCMeta, abstractmethod

from haas.model import *

# There's probably a better way to do this
from haas.test_common import newDB, releaseDB

class ModelTest:
    """Superclass with tests common to all models."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def sample_obj(self):
        """returns a sample object, which can be used for various tests.

        There aren't really any specific requirements for the object, just that
        it be "valid."
        """

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
        return Nic(Node('node-99'), 'ipmi', '00:11:22:33:44:55')


class TestNode(ModelTest):

    def sample_obj(self):
        return Node('node-99')


class TestProject(ModelTest):

    def sample_obj(self):
        return Project(Group('acme_corp'), 'manhattan')


class TestSwitch(ModelTest):

    def sample_obj(self):
        return Switch('dev-switch', 'acme_corp')


class TestHeadnode(ModelTest):

    def sample_obj(self):
        return Headnode(Project(Group('acme_corp'), 'anvil-nextgen'), 'hn-example')


class TestHnic(ModelTest):

    def sample_obj(self):
        return Hnic(Headnode(Project(Group('acme-corp'), 'anvil-nextgen'),
            'hn-0'), 'storage', '00:11:22:33:44:55')


class TestVlan(ModelTest):

    def sample_obj(self):
        return Vlan(102)


class TestNetwork(ModelTest):

    def sample_obj(self):
        return Network(Project(Group('acme_corp'), 'anvil-nextgen'), Vlan(102), 'hammernet')
