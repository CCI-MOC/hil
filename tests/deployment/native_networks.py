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

"""Deployment Unit Tests - These tests are intended for our
internal setup only and will most likely not work on
other HaaS configurations."""

from haas import api, model, deferred, server
from haas.model import db
from haas.test_common import *
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


site_layout = pytest.fixture(site_layout)

pytestmark = pytest.mark.usefixtures('configure',
                                     'server_init',
                                     'fresh_database',
                                     'with_request_context',
                                     'site_layout')


class TestNativeNetwork(NetworkTest):

    def test_isolated_networks(self):

        def create_networks():
            nodes = self.collect_nodes()

            # Create two networks
            network_create_simple('net-0', 'anvil-nextgen')
            network_create_simple('net-1', 'anvil-nextgen')

            ports = self.get_all_ports(nodes)

            # Assert that n0 and n1 are not on any network
            port_networks = self.get_port_networks(ports)

            assert self.get_network(nodes[0].nics[0].port, port_networks) == \
                set()
            assert self.get_network(nodes[1].nics[0].port, port_networks) == \
                set()

            # Connect n0 and n1 to net-0 and net-1 respectively
            api.node_connect_network(nodes[0].label,
                                     nodes[0].nics[0].label,
                                     'net-0')
            api.node_connect_network(nodes[1].label,
                                     nodes[1].nics[0].label,
                                     'net-1')
            deferred.apply_networking()

            # Assert that n0 and n1 are on isolated networks
            port_networks = self.get_port_networks(ports)
            assert self.get_network(nodes[0].nics[0].port, port_networks) == \
                set([nodes[0].nics[0].port])
            assert self.get_network(nodes[1].nics[0].port, port_networks) == \
                set([nodes[1].nics[0].port])

            # Add n2 and n3 to the same networks as n0 and n1 respectively
            api.node_connect_network(nodes[2].label,
                                     nodes[2].nics[0].label,
                                     'net-0')
            api.node_connect_network(nodes[3].label,
                                     nodes[3].nics[0].label,
                                     'net-1')
            deferred.apply_networking()

            # Assert that n2 and n3 have been added to n0 and n1's networks
            # respectively
            port_networks = self.get_port_networks(ports)
            assert self.get_network(nodes[0].nics[0].port, port_networks) == \
                set([nodes[0].nics[0].port, nodes[2].nics[0].port])
            assert self.get_network(nodes[1].nics[0].port, port_networks) == \
                set([nodes[1].nics[0].port, nodes[3].nics[0].port])

        def delete_networks():
            # Query the DB for nodes on this project
            project = api._must_find(model.Project, 'anvil-nextgen')
            nodes = project.nodes
            ports = self.get_all_ports(nodes)

            # Remove all nodes from their networks
            for node in nodes:
                attachment = model.NetworkAttachment.query \
                    .filter_by(nic=node.nics[0]).one()
                api.node_detach_network(node.label,
                                        node.nics[0].label,
                                        attachment.network.label)
            deferred.apply_networking()

            # Assert that none of the nodes are on any network
            port_networks = self.get_port_networks(ports)
            for node in nodes:
                assert self.get_network(node.nics[0].port, port_networks) == \
                    set()

            # Delete the networks
            api.network_delete('net-0')
            api.network_delete('net-1')

        # Create a project
        api.project_create('anvil-nextgen')

        create_networks()
        delete_networks()
