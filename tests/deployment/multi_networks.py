"""Test various properties re: vlan tagged networks, on real hardware.

For guidance on running these tests, see the section on deployment
tests in docs/testing.md
"""

import json

from hil import api, model, deferred, config
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


class TestMultiNets(NetworkTest):
    """NetworkTest using multiple tagged vlan networks on a port."""

    def test_multi_networks(self):
        """A suite of tests to ensure that multiple networks can relate
        to a single port. Previously, there was an issue with
        get_port_networks() where it didn't return the full range of
        vlans, rather it returned only the ones at the ends of the ranges.
        These tests ensure that the full range of vlans can be fetched.
        Issue: https://github.com/CCI-MOC/hil/issues/921
        See the inline comments for the specifics.
        """

        def get_legal_channels(network):
            """Get the legal channels for a network."""
            response_body = api.show_network(network)
            response_body = json.loads(response_body)
            return response_body['channels']

        def create_multi_nets():
            """Create multiple networks and connect them all to one port.

            Test that each network can be successfully added and discovered
            on the port.
            """

            nodes = self.collect_nodes()

            # create 5 networks
            for i in range(5):
                network_create_simple('net-%d' % i, 'anvil-nextgen')

            ports = self.get_all_ports(nodes)

            # assert that node 0 is not on any network
            port_networks = self.get_port_networks(ports)
            assert self.get_network(nodes[0].nics[0].port, port_networks) == \
                set()

            # get channel IDs for tagged versions of networks
            net_tag = {}
            for i in range(4):
                net_tag[i] = get_legal_channels('net-%d' % i)[1]

            # connect node 0 to net-0 in native mode
            api.node_connect_network(nodes[0].label,
                                     nodes[0].nics[0].label,
                                     'net-0')
            deferred.apply_networking()
            # connect node 0 to net-1 in tagged mode
            api.node_connect_network(nodes[0].label,
                                     nodes[0].nics[0].label,
                                     'net-1',
                                     channel=net_tag[1])
            deferred.apply_networking()
            # connect node 0 to net-2 in tagged mode
            api.node_connect_network(nodes[0].label,
                                     nodes[0].nics[0].label,
                                     'net-2',
                                     channel=net_tag[2])
            deferred.apply_networking()
            # connect node 0 to net-3 in tagged mode
            api.node_connect_network(nodes[0].label,
                                     nodes[0].nics[0].label,
                                     'net-3',
                                     channel=net_tag[3])
            deferred.apply_networking()

            # assert that all networks show up on the port
            port_networks = self.get_port_networks(ports)
            networks = \
                set([net for net,
                    _channel in port_networks.get(nodes[0].nics[0].port)])
            # create a list of networks with native net-0 included
            networks_added = set([get_legal_channels('net-0')[0],
                                 net_tag[1],
                                 net_tag[2], net_tag[3]])
            assert networks == networks_added

        def teardown():
            """Teardown the setup from create_multi_nets.
            """
            # Query the DB for nodes on this project
            project = api.get_or_404(model.Project, 'anvil-nextgen')
            nodes = project.nodes
            ports = self.get_all_ports(nodes)

            # Remove all nodes from their networks using port_revert.
            for node in nodes:
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

        create_multi_nets()
        teardown()
