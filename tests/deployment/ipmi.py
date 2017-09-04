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
"""Deployment tests for ipmi driver.

These require an actual HIL setup with a real node, and are
somewhat particular to the MOC's development environment. They may be
difficult to run in other contexts.
"""

from hil.test_common import config_testsuite, fresh_database, \
    fail_on_log_warnings, with_request_context, site_layout, server_init
from hil.model import Node
from hil import config, api
import pytest


@pytest.fixture
def configure():
    """Configure HIL"""
    config_testsuite()
    config.load_extensions()


fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)
fresh_database = pytest.fixture(fresh_database)
server_init = pytest.fixture(server_init)


with_request_context = pytest.yield_fixture(with_request_context)
site_layout = pytest.fixture(site_layout)

pytestmark = pytest.mark.usefixtures('configure',
                                     'server_init',
                                     'fresh_database',
                                     'with_request_context',
                                     'site_layout')


class TestIpmi():
    """ Test IPMI driver calls using functions included in the IPMI driver. """

    def collect_nodes(self):
        """Collects nodes in the free list."""
        free_nodes = Node.query.filter_by(project_id=None).all()
        return free_nodes

    def test_node_power_cycle(self):
        """Test power cycling nodes."""
        nodes = self.collect_nodes()
        for node in nodes:
            api.node_power_cycle(node.label)

    def test_node_power_force(self):
        """Test power cycling nodes, with force=True."""
        nodes = self.collect_nodes()
        for node in nodes:
            api.node_power_cycle(node.label, True)

    def test_node_power_off(self):
        """Test shutting down nodes properly"""
        nodes = self.collect_nodes()
        for node in nodes:
            api.node_power_off(node.label)

    def test_node_set_bootdev(self):
        """Test setting the boot device."""
        nodes = self.collect_nodes()
        for node in nodes:
            # change a node's bootdevice to a valid boot device
            api.node_set_bootdev(node.label, 'pxe')
            api.node_set_bootdev(node.label, 'disk')
            api.node_set_bootdev(node.label, 'none')
            # set the bootdevice to something invalid
            with pytest.raises(api.BadArgumentError):
                api.node_set_bootdev(node.label, 'invalid-device')

        # register a node with erroneous ipmi details to raise OBMError
        # XXX: In theory, this could actually be a real node; we should take
        # some measure to ensure this never collides with something actually
        # in our test setup.
        api.node_register('node-99-z4qa63', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        with pytest.raises(api.OBMError):
            api.node_set_bootdev('node-99-z4qa63', 'none')
