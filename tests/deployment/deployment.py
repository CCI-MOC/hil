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

from haas import api
from haas.test_common import *
import re
import pexpect


class TestHeadNode:

    @deployment_test
    @hnic_cleanup
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
    @hnic_cleanup
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
            vlans = []
            r_list = cfg.get('switch dell', 'vlans').split(",")
            for r in r_list:
                r = r.strip().split("-")
                if len(r) == 1:
                    vlans.append(int(r[0]))
                else:
                    for i in range(int(r[0]), int(r[1])+1):
                        vlans.append(int(i))

            vlan_cfgs = []
            for vlan in vlans:
                console.sendline('show vlan tag %d' % vlan)
                console.expect(cmd_prompt)
                vlan_cfgs.append(console.before)

            # close session
            console.sendline('exit')
            console.expect(pexpect.EOF)

            return vlan_cfgs

        def get_network(intfc, vlan_cfgs):
            """Returns all interfaces on a network"""
            for vlan_cfg in vlan_cfgs:
                if intfc in vlan_cfg:
                    regex = re.compile(r'gi\d+\/\d+\/\d+-?\d?\d?')
                    network = regex.findall(vlan_cfg)
                    # XXX: this probably shouldn't be hard-coded
                    network.remove('gi1/0/19')
                    return network
            return []
        
        def create_networks():
            api.group_create('acme-code')
            api.project_create('anvil-nextgen', 'acme-code')
            api.network_create('net-0', 'anvil-nextgen')
            api.network_create('net-1', 'anvil-nextgen')    
            for node in range(195, 199):
                api.project_connect_node('anvil-nextgen', node)
    
            # Ask the switch which vlans nodes 195 and 196 are on
            vlan_cfgs = get_switch_vlans()
            node_195_net = get_network('gi1/0/15', vlan_cfgs)
            node_196_net= get_network('gi1/0/16', vlan_cfgs)
    
            # Assert that nodes 195 and 196 are not on a network
            assert node_195_net == []
            assert node_196_net == []
    
            # Add nodes 195 and 196 to net-0 and net-1 respectively
            api.node_connect_network('195', 'node-195-nic1', 'net-0')
            api.node_connect_network('196', 'node-196-nic1', 'net-1')
            
            # Apply current configuration
            api.project_apply('anvil-nextgen')
    
            # Ask the switch which vlans nodes 195 anf 196 are on
            vlan_cfgs = get_switch_vlans()
    
            print(vlan_cfgs[0])
    
            node_195_net = get_network('gi1/0/15', vlan_cfgs)
            node_196_net = get_network('gi1/0/16', vlan_cfgs)
    
            # Assert that nodes 195 and 196 are on isolated networks
            assert node_195_net == ['gi1/0/15']
            assert node_196_net == ['gi1/0/16']
    
            # Add nodes 197 and 198 to the same networks as nodes 195 and 196 respectively
            api.node_connect_network('197', 'node-197-nic1', 'net-0')
            api.node_connect_network('198', 'node-198-nic1', 'net-1')
    
            # Apply current configuration
            api.project_apply('anvil-nextgen')
    
            # Ask the switch which vlans nodes 195 and 196 are on
            vlan_cfgs = get_switch_vlans() 
            node_195_net = get_network('gi1/0/15', vlan_cfgs)
            node_196_net = get_network('gi1/0/16', vlan_cfgs)
    
            # Assert that nodes 197 and 198 have been added to nodes 195 and 196's networks respectively
            assert node_195_net == ['gi1/0/15', 'gi1/0/17']
            assert node_196_net == ['gi1/0/16', 'gi1/0/18']


        def delete_networks():
            # Remove all nodes from their networks
            for node in range(195,199):
                api.node_detach_network(node, 'node-%d-nic1' % node)
    
            # Apply current configuration
            api.project_apply('anvil-nextgen')
    
            # Ask the switch which vlans nodes 195, 196, 197 and 198 are on
            vlan_cfgs = get_switch_vlans()
            node_195_net = get_network('gi1/0/15', vlan_cfgs)
            node_196_net = get_network('gi1/0/16', vlan_cfgs)
            node_197_net = get_network('gi1/0/17', vlan_cfgs)
            node_198_net = get_network('gi1/0/18', vlan_cfgs)
    
            # Assert that nodes 195, 196, 197, and 198 are not on a network
            assert node_195_net == []
            assert node_196_net == []
            assert node_197_net == []
            assert node_198_net == []
    
            # Delete the networks
            api.network_delete('net-0')
            api.network_delete('net-1')
            
            # Apply current configuration
            api.project_apply('anvil-nextgen')

        try:
            # Run core tests
            create_networks()
        finally:
            # Always cleanup and run final tests
            delete_networks()

    @deployment_test
    @hnic_cleanup
    def test_network_allocation(self, db):
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        for network in range(0,11):
            api.network_create('net-%d' %network, 'anvil-nextgen')
 
        # Ensure that error is raised if too many networks allocated
        with pytest.raises(api.AllocationError):
            api.network_create('net-11', 'anvil-nextgen')
 
        # Ensure that project_apply doesn't affect network allocation
        api.project_apply('anvil-nextgen')
        with pytest.raises(api.AllocationError):
            api.network_create('net-11', 'anvil-nextgen')
 
        # Ensure that network_delete doesn't affect network allocation
        api.network_delete('net-10')
        api.network_create('net-10', 'anvil-nextgen')
        with pytest.raises(api.AllocationError):
            api.network_create('net-11', 'anvil-nextgen')
 
        # Ensure that network_delete+project_apply doesn't affect network
        # allocation
        api.network_delete('net-10')
        api.project_apply('anvil-nextgen')
        api.network_create('net-10', 'anvil-nextgen')
        with pytest.raises(api.AllocationError):
            api.network_create('net-11', 'anvil-nextgen')

        api.network_delete('net-10')
        api.network_create('net-10', 'anvil-nextgen')
        api.project_apply('anvil-nextgen')
        with pytest.raises(api.AllocationError):
            api.network_create('net-11', 'anvil-nextgen')

        # Clean up networks
        for network in range(0,11):
            api.network_delete('net-%d' % network)
        api.project_apply('anvil-nextgen')
