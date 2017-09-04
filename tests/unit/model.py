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

from hil.model import Node, Nic, Project, Headnode, Hnic, Network, \
    NetworkingAction, Metadata
from hil import config

from hil.test_common import fresh_database, config_testsuite, ModelTest, \
    fail_on_log_warnings
import pytest

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


@pytest.fixture
def configure():
    """Configure HIL."""
    config_testsuite()
    config.load_extensions()


fresh_database = pytest.fixture(fresh_database)


pytestmark = pytest.mark.usefixtures('configure', 'fresh_database')


class TestNic(ModelTest):
    """ModelTest for Nic objects."""

    def sample_obj(self):
        from hil.ext.obm.ipmi import Ipmi
        return Nic(Node(label='node-99',
                        obm=Ipmi(type=Ipmi.api_name,
                                 host="ipmihost",
                                 user="root",
                                 password="tapeworm")),
                   'ipmi', '00:11:22:33:44:55')


class TestNode(ModelTest):
    """ModelTest for Node objects."""

    def sample_obj(self):
        from hil.ext.obm.ipmi import Ipmi
        return Node(label='node-99',
                    obm=Ipmi(type=Ipmi.api_name,
                             host="ipmihost",
                             user="root",
                             password="tapeworm"))


class TestProject(ModelTest):
    """ModelTest for Project objects."""

    def sample_obj(self):
        return Project('manhattan')


class TestHeadnode(ModelTest):
    """ModelTest for Headnode objects."""

    def sample_obj(self):
        return Headnode(Project('anvil-nextgen'),
                        'hn-example', 'base-headnode')


class TestHnic(ModelTest):
    """ModelTest for Hnic objects."""

    def sample_obj(self):
        return Hnic(Headnode(Project('anvil-nextgen'),
                             'hn-0', 'base-headnode'),
                    'storage')


class TestNetwork(ModelTest):
    """ModelTest for Network objects."""

    def sample_obj(self):
        pj = Project('anvil-nextgen')
        return Network(pj, [pj], True, '102', 'hammernet')


class TestMetadata(ModelTest):
    """ModelTest for Metadata objects."""

    def sample_obj(self):
        from hil.ext.obm.ipmi import Ipmi
        node = Node(label='node-99',
                    obm=Ipmi(type=Ipmi.api_name,
                             host="ipmihost",
                             user="root",
                             password="tapeworm"))
        return Metadata('EK', 'pk', node)


class TestNetworkingAction(ModelTest):
    """ModelTest for NetworkingAction objects."""

    def sample_obj(self):
        from hil.ext.obm.ipmi import Ipmi
        nic = Nic(Node(label='node-99',
                       obm=Ipmi(type=Ipmi.api_name,
                                host="ipmihost",
                                user="root",
                                password="tapeworm")),
                  'ipmi', '00:11:22:33:44:55')
        project = Project('anvil-nextgen')
        network = Network(project, [project], True, '102', 'hammernet')
        return NetworkingAction(nic=nic,
                                new_network=network,
                                channel='null')
