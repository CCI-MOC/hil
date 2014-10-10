# Copyright 2013-2014 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

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
from haas.test_common import newDB, releaseDB, database_only

class ModelTest:
    """Superclass with tests common to all models.

    Inheriting from ``ModelTest`` will generate tests in the subclass (each
    of the methods beginning with ``test_`` below), but the ``ModelTest`` class
    itself does not generate tests. (pytest will ignore it because the name of
    the class does not start with ``Test`).
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def sample_obj(self):
        """returns a sample object, which can be used for various tests.

        There aren't really any specific requirements for the object, just that
        it be "valid."
        """

    def test_repr(self):
        print(self.sample_obj())

    @database_only
    def test_insert(self, db):
        db.add(self.sample_obj())


class TestUsers(ModelTest):
    """Test user-related functionality"""

    def sample_obj(self):
        return User('bob', 'secret')


class TestNic(ModelTest):

    def sample_obj(self):
        return Nic(Node('node-99', 'ipmihost', 'root', 'tapeworm'),
                   'ipmi', '00:11:22:33:44:55')


class TestNode(ModelTest):

    def sample_obj(self):
        return Node('node-99', 'ipmihost', 'root', 'tapeworm')


class TestProject(ModelTest):

    def sample_obj(self):
        return Project('manhattan')


class TestHeadnode(ModelTest):

    def sample_obj(self):
        return Headnode(Project('anvil-nextgen'), 'hn-example', 'base-headnode')


class TestHnic(ModelTest):

    def sample_obj(self):
        return Hnic(Headnode(Project('anvil-nextgen'),
            'hn-0', 'base-headnode'), 'storage')


class TestNetwork(ModelTest):

    def sample_obj(self):
        pj = Project('anvil-nextgen')
        return Network(pj, pj, True, '102', 'hammernet')
