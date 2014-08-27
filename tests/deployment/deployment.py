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

from haas import api, model
from haas.drivers.dell import get_vlan_list
from haas.test_common import *
import json
import pexpect
import pytest
import re

class TestHeadNode:

    @deployment_test
    @headnode_cleanup
    def test_headnode_start(self, db):
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.network_create('spider-web', 'anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hnic-0', 'de:ad:be:ef:20:14')
        api.headnode_connect_network('hn-0', 'hnic-0', 'spider-web')
        api.headnode_start('hn-0')


class TestNetwork:

    @deployment_test
    @headnode_cleanup
    def test_isolated_networks(self, db):

        def get_switch_vlans():
            # load the configuration:
            switch_ip = cfg.get('switch dell', 'ip')
            switch_user = cfg.get('switch dell', 'user')
            switch_pass = cfg.get('switch dell', 'pass')

            # connect to the switch, and log in:
            console = pexpect.spawn('telnet ' + switch_ip)
            console.expect('User Name:')
            console.sendline(switch_user)
            console.expect('Password:')
            console.sendline(switch_pass)

            #Regex to handle different prompt at switch 
            #[\r\n]+ will handle any newline
            #.+ will handle any character after newline 
            # this sequence terminates with #
            console.expect(r'[\r\n]+.+#')
            cmd_prompt = console.after
            cmd_prompt = cmd_prompt.strip(' \r\n\t')

            # get possible vlans from config
            vlan_cfgs = []
            for vlan in get_vlan_list():
                console.sendline('show vlan tag %d' % vlan)
                console.expect(cmd_prompt)
                vlan_cfgs.append(console.before)

            # close session
            console.sendline('exit')
            console.expect(pexpect.EOF)

            return vlan_cfgs

        def get_network(intfc, vlan_cfgs):
            """Returns all interfaces on a network"""
            trunk_port = cfg.get('switch dell', 'trunk_port')
            for vlan_cfg in vlan_cfgs:
                if intfc in vlan_cfg:
                    regex = re.compile(r'gi\d+\/\d+\/\d+-?\d?\d?')
                    network = regex.findall(vlan_cfg)
                    network.remove(trunk_port)
                    return network
            return []
        
        def create_networks(nodes):
            # At least 2 nodes with 1 nic each are required for this test
            if len(nodes) < 2:
                return

            # Create two networks
            api.network_create('net-0', 'anvil-nextgen')
            api.network_create('net-1', 'anvil-nextgen')
 
            # Define nodes n0 and n1, their nic, and their port
            n0 = nodes[0].label
            n1 = nodes[1].label
            n0_nic = nodes[0].nics[0].label
            n1_nic = nodes[1].nics[0].label
            n0_port = nodes[0].nics[0].port.label
            n1_port = nodes[1].nics[0].port.label
            
            # Assert that n0 and n1 are not on any network
            vlan_cfgs = get_switch_vlans()
            assert get_network(n0_port, vlan_cfgs) == []
            assert get_network(n0_port, vlan_cfgs) == []

            # Connect n0 and n1 to net-0 and net-1 respectively
            api.node_connect_network(n0, n0_nic, 'net-0')
            api.node_connect_network(n1, n1_nic, 'net-1')
            
            # Apply current configuration
            api.project_apply('anvil-nextgen')
    
            # Assert that n0 and n1 are on isolated networks
            vlan_cfgs = get_switch_vlans()
            assert get_network(n0_port, vlan_cfgs) == [n0_port]
            assert get_network(n1_port, vlan_cfgs) == [n1_port]
    
            # At least 4 nodes with 1 nic each are required for further testing
            if len(nodes) < 4:
                return
       
            # Define nodes n2 and n3, their nic, and their port
            n2 = nodes[2].label
            n3 = nodes[3].label
            n2_nic = nodes[2].nics[0].label
            n3_nic = nodes[3].nics[0].label
            n2_port = nodes[2].nics[0].port.label
            n3_port = nodes[3].nics[0].port.label 

            # Add n2 and n3 to the same networks as n0 and n1 respectively
            api.node_connect_network(n2, n2_nic, 'net-0')
            api.node_connect_network(n3, n3_nic, 'net-1')
    
            # Apply current configuration
            api.project_apply('anvil-nextgen')
    
            # Assert that n2 and n3 have been added to n0 and n1's networks
            # respectively
            vlan_cfgs = get_switch_vlans() 
            assert get_network(n0_port, vlan_cfgs) == [n0_port, n2_port]
            assert get_network(n1_port, vlan_cfgs) == [n1_port, n3_port]


        def delete_networks(nodes):
            # Remove all nodes from their networks
            for node in nodes:
                api.node_detach_network(node.label, node.nics[0].label)
    
            # Apply current configuration
            api.project_apply('anvil-nextgen')
    
            # Assert that none of the nodes are on any network
            vlan_cfgs = get_switch_vlans()
            for node in nodes:
                assert get_network(node.nics[0].label, vlan_cfgs) == []
    
            # Delete the networks
            api.network_delete('net-0')
            api.network_delete('net-1')
            
            # Apply current configuration
            api.project_apply('anvil-nextgen')

        
        # Create group and project
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        
        # Add up to 4 available nodes with nics to the project
        free_nodes = db.query(model.Node).filter_by(project_id=None).all()
        nodes = []
        for node in free_nodes:
            if len(node.nics) > 0:
                api.project_connect_node('anvil-nextgen', node.label)
                nodes.append(node)
                if len(nodes) >= 4:
                    break
        
        # Try the create_networks tests, then always run the delete_networks
        # tests
        try:
            create_networks(nodes)
        finally:
            delete_networks(nodes)

    @deployment_test
    @headnode_cleanup
    def test_network_allocation(self, db):
        try:
            api.group_create('acme-code')
            api.project_create('anvil-nextgen', 'acme-code')
            
            vlans = get_vlan_list()
            num_vlans = len(vlans)

            for network in range(0,num_vlans):
                api.network_create('net-%d' % network, 'anvil-nextgen')
     
            # Ensure that error is raised if too many networks allocated
            with pytest.raises(api.AllocationError):
                api.network_create('net-%d' % num_vlans, 'anvil-nextgen')
     
            # Ensure that project_apply doesn't affect network allocation
            api.project_apply('anvil-nextgen')
            with pytest.raises(api.AllocationError):
                api.network_create('net-%d' % num_vlans, 'anvil-nextgen')
     
            # Ensure that network_delete doesn't affect network allocation
            api.network_delete('net-%d' % (num_vlans-1))
            api.network_create('net-%d' % (num_vlans-1), 'anvil-nextgen')
            with pytest.raises(api.AllocationError):
                api.network_create('net-%d' % num_vlans, 'anvil-nextgen')
     
            # Ensure that network_delete+project_apply doesn't affect network
            # allocation
            api.network_delete('net-%d' % (num_vlans-1))
            api.project_apply('anvil-nextgen')
            api.network_create('net-%d' % (num_vlans-1), 'anvil-nextgen')
            with pytest.raises(api.AllocationError):
                api.network_create('net-%d' % num_vlans, 'anvil-nextgen')
    
            api.network_delete('net-%d' % (num_vlans-1))
            api.network_create('net-%d' % (num_vlans-1), 'anvil-nextgen')
            api.project_apply('anvil-nextgen')
            with pytest.raises(api.AllocationError):
                api.network_create('net-%d' % num_vlans, 'anvil-nextgen')

        finally:
            # Clean up networks
            for network in range(0,num_vlans):
                api.network_delete('net-%d' % network)
            api.project_apply('anvil-nextgen')
