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

"""Test various properties re: vlan tagged networks, on real hardware.

For guidance on running these tests, see the section on deployment
tests in docs/testing.md
"""

import json

from collections import namedtuple
from hil import api, model, deferred, config, errors
from hil.test_common import config_testsuite, fail_on_log_warnings, \
    fresh_database, with_request_context, site_layout, NetworkTest, \
    network_create_simple, server_init
import pytest


@pytest.fixture
def configure():
    """Configure HIL."""
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


class TestNetworkVlan(NetworkTest):
    """NetworkTest using tagged vlan networks."""

    def test_isolated_networks(self):
        """Do a bunch of network operations on the switch, and verify things
        along the way.

        The above is super vague; unfortunately the setup operations are very
        slow, so it makes a huge difference to do everything in one pass. See
        the comments in-line to understand exactly what is being tested.
        """

        def get_legal_channels(network):
            """Get the legal channels for a network."""
            response_body = api.show_network(network)
            response_body = json.loads(response_body)
            return response_body['channels']

        def create_networks():
            """Create networks and connect things to them.

            Test various things along the way.
            """
            nodes = self.collect_nodes()

            # Create four networks
            network_create_simple('net-0', 'anvil-nextgen')
            network_create_simple('net-1', 'anvil-nextgen')
            network_create_simple('net-2', 'anvil-nextgen')
            network_create_simple('net-3', 'anvil-nextgen')

            ports = self.get_all_ports(nodes)
            # get the switch name from any of the nics
            switch = nodes[0].nics[0].port.owner

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
            net_tag[2] = get_legal_channels('net-2')[1]

            # Connect node 0 to net-0 (native mode)
            api.node_connect_network(nodes[0].label,
                                     nodes[0].nics[0].label,
                                     'net-0')

            # before connecting node 1 to net-1 in tagged mode, we must check
            # if the switch supports nativeless trunk mode; if not, then we
            # add some native network and perform additional checks before
            # proceeding.
            if 'nativeless-trunk-mode' not in switch.get_capabilities():
                # connecting the first network as tagged should raise an error
                with pytest.raises(errors.BlockedError):
                    api.node_connect_network(nodes[1].label,
                                             nodes[1].nics[0].label,
                                             'net-2',
                                             channel=net_tag[2])
                api.node_connect_network(nodes[1].label,
                                         nodes[1].nics[0].label,
                                         'net-2')
                deferred.apply_networking()

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
            if 'nativeless-trunk-mode' not in switch.get_capabilities():
                api.node_connect_network(nodes[2].label,
                                         nodes[2].nics[0].label,
                                         'net-3')
                deferred.apply_networking()
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

            # at this point, node-2 is connected to net-0 (tagged)
            # and depending on the switch, to net-3 (native). Let's connect it
            # to net-1 (tagged) (which node-1 is connected to)
            api.node_connect_network(nodes[2].label,
                                     nodes[2].nics[0].label,
                                     'net-1',
                                     channel=net_tag[1])
            deferred.apply_networking()
            port_networks = self.get_port_networks(ports)
            # assert that node-2 was added to node-1's network correctly.
            assert self.get_network(nodes[1].nics[0].port, port_networks) == \
                set([nodes[1].nics[0].port,
                     nodes[2].nics[0].port,
                     nodes[3].nics[0].port])

        def delete_networks():
            """Tear down things set up by create_networks

            again, we do various checks along the way.
            """
            # Query the DB for nodes on this project
            project = api._must_find(model.Project, 'anvil-nextgen')
            nodes = project.nodes
            ports = self.get_all_ports(nodes)

            # Remove all nodes from their networks. We do this in two ways, to
            # test the different mechanisms.

            # For the first two nodes, we first build up a list of
            # the arguments to the API calls, which has no direct references to
            # database objects, and then make the API calls and invoke
            # deferred.apply_networking after. This is important --
            # The API calls and apply_networking normally run in their own
            # transaction. We get away with not doing this in the tests because
            # we serialize everything ourselves, so there's no risk of
            # interference. If we were to hang on to references to database
            # objects across such calls however, things could get harry.
            all_attachments = []
            net = namedtuple('net', 'node nic network channel')
            for node in nodes[:2]:
                attachments = model.NetworkAttachment.query \
                    .filter_by(nic=node.nics[0]).all()
                for attachment in attachments:
                    all_attachments.append(
                                        net(node=node.label,
                                            nic=node.nics[0].label,
                                            network=attachment.network.label,
                                            channel=attachment.channel))

            switch = nodes[0].nics[0].port.owner
            # in some switches, the native network can only be disconnected
            # after we remove all tagged networks first. The following checks
            # for that and rearranges the networks (all_attachments) such that
            # tagged networks are removed first.

            if 'nativeless-trunk-mode' not in switch.get_capabilities():
                # sort by channel; vlan/<integer> comes before vlan/native
                # because the ASCII for numbers comes before ASCII for letters.
                all_attachments = sorted(all_attachments,
                                         key=lambda net: net.channel)

            for attachment in all_attachments:
                api.node_detach_network(attachment.node, attachment.nic,
                                        attachment.network)
                deferred.apply_networking()

            # For the second two nodes, we just call port_revert on the nic's
            # port.
            for node in nodes[2:]:
                port = node.nics[0].port
                api.port_revert(port.owner.label, port.label)
            deferred.apply_networking()

            # Assert that none of the nodes are on any network
            port_networks = self.get_port_networks(ports)
            for node in nodes:
                assert self.get_network(node.nics[0].port, port_networks) == \
                    set()

            # Delete the networks
            api.network_delete('net-0')
            api.network_delete('net-1')
            api.network_delete('net-2')
            api.network_delete('net-3')

        # Create a project
        api.project_create('anvil-nextgen')

        create_networks()
        delete_networks()
