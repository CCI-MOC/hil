# Copyright 2017 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language
# governing permissions and limitations under the License.
"""Unit tests for dell switches running Dell Networking OS 9 (with REST API)"""

import pytest

from hil import model, api, config
from hil.model import db
from hil.test_common import config_testsuite, config_merge, fresh_database, \
    fail_on_log_warnings, with_request_context, server_init, \
    network_create_simple
from hil.errors import BlockedError

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)
fresh_database = pytest.fixture(fresh_database)
server_init = pytest.fixture(server_init)
with_request_context = pytest.yield_fixture(with_request_context)

SWITCH_TYPE = 'http://schema.massopencloud.org/haas/v0/switches/dellnos9'


@pytest.fixture
def configure():
    """Configure HIL"""
    config_testsuite()
    config_merge({
        'auth': {
            'require_authentication': 'True',
        },
        'extensions': {
            'hil.ext.auth.null': '',
            'hil.ext.switches.dellnos9': '',
            'hil.ext.obm.mock': '',
            'hil.ext.network_allocators.null': None,
            'hil.ext.network_allocators.vlan_pool': '',
        },
        'hil.ext.network_allocators.vlan_pool': {
            'vlans': '40-80',
        },
    })
    config.load_extensions()


default_fixtures = ['fail_on_log_warnings',
                    'configure',
                    'fresh_database',
                    'server_init',
                    'with_request_context']

pytestmark = pytest.mark.usefixtures(*default_fixtures)


def test_ensure_legal_operations():
    """Test to ensure that ensure_legal_operations works as expected"""

    # create a project and a network
    api.project_create('anvil-nextgen')
    network_create_simple('hammernet', 'anvil-nextgen')
    network_create_simple('pineapple', 'anvil-nextgen')

    # register a switch of type dellnos9 and add a port to it
    api.switch_register('s3048',
                        type=SWITCH_TYPE,
                        username="switch_user",
                        password="switch_pass",
                        hostname="switchname",
                        interface_type="GigabitEthernet")
    api.switch_register_port('s3048', '1/3')
    switch = api._must_find(model.Switch, 's3048')

    # register a ndoe and a nic
    api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/mock",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
    api.project_connect_node('anvil-nextgen', 'compute-01')
    api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
    nic = api._must_find(model.Nic, 'eth0')

    api.port_connect_nic('s3048', '1/3', 'compute-01', 'eth0')

    # connecting a trunked network wihtout having a native should fail.
    # call the method directly and test the API too.
    with pytest.raises(BlockedError):
        switch.ensure_legal_operation(nic, 'connect', 'vlan/1212')

    with pytest.raises(BlockedError):
        api.node_connect_network('compute-01', 'eth0', 'hammernet', 'vlan/40')

    # put a trunked and native network in the database, and then try to remove
    # the native network first
    db.session.add(model.NetworkAttachment(
                nic=nic,
                network=api._must_find(model.Network, 'hammernet'),
                channel='vlan/native'))

    db.session.add(model.NetworkAttachment(
                nic=nic,
                network=api._must_find(model.Network, 'pineapple'),
                channel='vlan/40'))

    with pytest.raises(BlockedError):
        switch.ensure_legal_operation(nic, 'detach', 'vlan/native')

    with pytest.raises(BlockedError):
        api.node_detach_network('compute-01', 'eth0', 'hammernet')
