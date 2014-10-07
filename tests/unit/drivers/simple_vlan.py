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

"""Unit tests for VLAN helper functions"""

from functools import wraps

from haas import model, api
from haas.test_common import *
import pytest

from haas.config import cfg

from haas.drivers.simple_vlan import *

def vlan_test(vlan_list):
    """A decorator for tests of the simple_vlan driver.  Pass in a string for
    the vlan_list configuration option, which determines which vlans can be
    used for networking.
    """

    def dec(f):
        def config_initialize():
            # Use the 'dell' backend for these tests
            cfg.add_section('general')
            cfg.set('general', 'driver', 'simple_vlan')
            cfg.add_section('vlan')
            cfg.set('vlan', 'vlans', vlan_list)
            cfg.add_section('driver simple_vlan')
            cfg.set('driver simple_vlan', 'switch', '{"switch":"null"}')
            cfg.add_section('devel')
            cfg.set('devel', 'dry_run')

        @wraps(f)
        @clear_configuration
        def wrapped(self):
            config_initialize()
            db = newDB()
            f(self, db)
            releaseDB(db)

        return wrapped

    return dec

class TestSimpleVLAN:
    """Tests basic operation of Simple VLAN driver"""

    @vlan_test('84')
    def test_simple_vlan_network_operations(self, db):
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.switch_register('sw01', 'simple_vlan')
        for k in range(97,100):
            nodename = 'node-' + str(k)
            api.node_register(nodename, 'ipmihost', 'root', 'tapeworm')
            api.node_register_nic(nodename, 'eth0', 'DE:AD:BE:EF:20:14')
            api.project_connect_node('anvil-nextgen', nodename)
            api.port_register('sw01', nodename)
            api.port_connect_nic('sw01', nodename, nodename, 'eth0')
        api.project_detach_node('anvil-nextgen', 'node-97')
        api.node_connect_network('node-98', 'eth0', 'hammernet')
