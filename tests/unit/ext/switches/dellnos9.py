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


def mock_networking_action():
    """performs the required db operations and clears up the networking action
    queue, so that we can queue more items to test the api.the

    This is useful because calling deferred.apply_networking would require a
    real switch
    """
    action = db.session.query(model.NetworkingAction) \
        .order_by(model.NetworkingAction.id).one_or_none()

    if action.new_network is None:
            db.session.query(model.NetworkAttachment) \
                .filter_by(nic=action.nic, channel=action.channel)\
                .delete()
    else:
            db.session.add(model.NetworkAttachment(
                nic=action.nic,
                network=action.new_network,
                channel=action.channel))

    db.session.delete(action)
    db.session.commit()


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

    # doing these operations in the correct order, that is native network first
    # and then trunked, should work.
    api.node_connect_network('compute-01', 'eth0', 'hammernet', 'vlan/native')
    mock_networking_action()
    api.node_connect_network('compute-01', 'eth0', 'pineapple', 'vlan/41')
    mock_networking_action()

    # removing these networks in the wrong order should not work.
    with pytest.raises(BlockedError):
        switch.ensure_legal_operation(nic, 'detach', 'vlan/native')

    with pytest.raises(BlockedError):
        api.node_detach_network('compute-01', 'eth0', 'hammernet')

    # removing networks in the right order should work
    api.node_detach_network('compute-01', 'eth0', 'pineapple')
    mock_networking_action()
    api.node_detach_network('compute-01', 'eth0', 'hammernet')
    mock_networking_action()
    db.session.close()


def test_get_vlans():
    """Check that _get_vlans correctly parses the response to grab all VLANs"""
    from hil.ext.switches.dellnos9 import DellNOS9

    class MockDellNOS9(DellNOS9):
        """This class inherits from the DellNOS9 switch and then overrides
        some of the methods to return mock outputs. Makes it easier to write
        unit tests"""

        def _get_port_info(self, interface):
            """Returns mock port info"""
            ret = u"<outputxmlns='http://www.dell.com/ns/dell:0.1/root'>\n  \
            <command>show interfaces switchport GigabitEthernet1/3\r\n\r\n \
            Codes: U-Untagged T-Tagged\r\n x-Dot1x untagged,X-Dot1xtagged\r\n \
            G-GVRP tagged,M-Trunk\r\n i-Internal untagged, I-Internaltagged, \
            v-VLTuntagged, V-VLTtagged\r\n\r\n Name:GigabitEthernet1/3\r\n \
             802.1QTagged:Hybrid\r\n Vlan membership:\r\n Q Vlans\r\n U 1512 \
             \r\n T " + interface + "\r\n\r\n Native Vlan Id: 1512.\r\n\r\n \
            \r\n\r\nMOC-Dell-S3048-ON#</command>\n</output>\n"
            return ret.replace(' ', '')

        def _is_port_on(self, port):
            return True

    # get a switch object
    switch = MockDellNOS9()
    # check that various combinations of tagged and untagged vlans are
    # correctly parsed.
    assert switch._get_native_vlan('mock-interface') == ('vlan/native', '1512')

    assert switch._get_vlans('10') == [('vlan/10', '10')]
    assert switch._get_vlans('10,20') == [('vlan/10', '10'), ('vlan/20', '20')]
    assert switch._get_vlans('10, 20-23, 25') == [
        ('vlan/10', '10'), ('vlan/20', '20'), ('vlan/21', '21'),
        ('vlan/22', '22'), ('vlan/23', '23'), ('vlan/25', '25')]
    assert switch._get_vlans('10-13') == [
        ('vlan/10', '10'), ('vlan/11', '11'),
        ('vlan/12', '12'), ('vlan/13', '13')]
    # just in case if the switch returns a 2 vlan range.
    assert switch._get_vlans('10-11') == [('vlan/10', '10'), ('vlan/11', '11')]
