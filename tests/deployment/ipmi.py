# Copyright 2013-2015 Massachusetts Open Cloud Contributors
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
"""Unit tests for headnodes.

These require an actual libvirt daemon (and full HaaS setup), and are
somewhat particular to the MOC's development environment. They may be
difficult to run in other contexts.
"""

from haas.test_common import *
from haas import config, server, rest
import pytest


@pytest.fixture
def configure():
    config_testsuite()
    config.load_extensions()


fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)
fresh_database = pytest.fixture(fresh_database)


@pytest.fixture
def server_init():
    server.register_drivers()
    server.validate_state()


with_request_context = pytest.yield_fixture(with_request_context)


headnode_cleanup = pytest.fixture(headnode_cleanup)
pytestmark = pytest.mark.usefixtures('configure',
                                     'server_init',
                                     'fresh_database',
                                     'with_request_context',
                                     'headnode_cleanup')


class TestIpmi():
    """ Test IPMI driver calls using functions included in the IPMI driver. """

    def collect_nodes(self):
        """Collects nodes in the free list."""
        free_nodes = Node.query.filter_by(project_id=None).all()
        return free_nodes

    def test_node_power_cycle(self):
        nodes = self.collect_nodes()
        for node in nodes:
            api.node_power_cycle(node.label)

    def test_node_power_off(self):
        nodes = self.collect_nodes()
        for node in nodes:
            api.node_power_off(node.label)
