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


def _test_node():
    """Generate a test node.

    In addition to `TestNode`, several of the other objects require a node,
    so we re-use the same one.
    """
    return Node(label='node-99',
                obmd_uri='https://obmd.example.com/node/node-99',
                # arbitrary:
                obmd_admin_token='b6a8a4e183fe26936efcd386e938cbfb')


class TestNode(ModelTest):
    """ModelTest for Node objects."""

    def sample_obj(self):
        return _test_node()


class TestNic(ModelTest):
    """ModelTest for Nic objects."""

    def sample_obj(self):
        return Nic(_test_node(), 'ipmi', '00:11:22:33:44:55')


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
        return Metadata('EK', 'pk', _test_node())


class TestNetworkingAction(ModelTest):
    """ModelTest for NetworkingAction objects."""

    def sample_obj(self):
        nic = Nic(_test_node(), 'ipmi', '00:11:22:33:44:55')
        project = Project('anvil-nextgen')
        network = Network(project, [project], True, '102', 'hammernet')
        return NetworkingAction(nic=nic,
                                new_network=network,
                                channel='null')
