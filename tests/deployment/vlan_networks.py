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

"""Deployment Unit Tests - These tests are intended for our
internal setup only and will most likely not work on
other HaaS configurations."""

from haas import api, model, deferred, server
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


class TestNetworkVlan(NetworkTest):

    def test_isolated_networks(self):

        def get_legal_channels(network):
            response_body = api.show_network(network)
            response_body = json.loads(response_body)
            return response_body['channels']

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

            # Get the channel ids for the tagged versions of the networks:
            net_tag = {}
            net_tag[0] = get_legal_channels('net-0')[1]
            net_tag[1] = get_legal_channels('net-1')[1]

            # Connect node 0 to net-0 (native mode)
            api.node_connect_network(nodes[0].label,
                                     nodes[0].nics[0].label,
                                     'net-0')
            # Connect node 1 to net-1 (tagged mode)
            api.node_connect_network(nodes[1].label,
                                     nodes[1].nics[0].label,
                                     'net-1',
                                     channel=net_tag[1])
            deferred.apply_networking()

            # Assert that n0 and n1 are on isolated networks
            port_networks = self.get_port_networks(ports)
            assert self.get_network(nodes[0].nics[0].port, port_networks) == \
                set([nodes[0].nics[0].port])
            assert self.get_network(nodes[1].nics[0].port, port_networks) == \
                set([nodes[1].nics[0].port])

            # Add n2 and n3 to the same networks as n0 and n1 respectively, but
            # with different channels (native vs. tagged)
            api.node_connect_network(nodes[2].label,
                                     nodes[2].nics[0].label,
                                     'net-0',
                                     channel=net_tag[0])
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

            # Verify that we can put nodes on more than one network, with
            # different channels:
            api.node_connect_network(nodes[2].label,
                                     nodes[2].nics[0].label,
                                     'net-1')
            deferred.apply_networking()
            port_networks = self.get_port_networks(ports)
            assert self.get_network(nodes[1].nics[0].port, port_networks) == \
                set([nodes[1].nics[0].port,
                     nodes[2].nics[0].port,
                     nodes[3].nics[0].port])

        def delete_networks():
            # Query the DB for nodes on this project
            project = api._must_find(model.Project, 'anvil-nextgen')
            nodes = project.nodes
            ports = self.get_all_ports(nodes)

            # Remove all nodes from their networks. We first build up a list of
            # the arguments to the API calls, which has no direct references to
            # database objects, and then make the API calls and invoke
            # deferred.apply_networking after. This is important --
            # The API calls and apply_networking normally run in their own
            # transaction. We get away with not doing this in the tests because
            # we serialize everything ourselves, so there's no risk of
            # interference. If we were to hang on to references to database
            # objects across such calls however, things could get harry.
            all_attachments = []
            for node in nodes:
                attachments = model.NetworkAttachment.query \
                    .filter_by(nic=node.nics[0]).all()
                for attachment in attachments:
                    all_attachments.append((node.label,
                                            node.nics[0].label,
                                            attachment.network.label))
            for attachment in all_attachments:
                api.node_detach_network(*attachment)
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
