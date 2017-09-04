# Copyright 2016 Massachusetts Open Cloud Contributors
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
"""Tests for the brocade switch driver"""

import pytest
import requests_mock

from hil import model
from hil.test_common import fail_on_log_warnings

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


MODE_RESPONSE_ACCESS = """
<mode xmlns="urn:brocade.com:mgmt:brocade-interface"
      xmlns:y="http://brocade.com/ns/rest"
      y:self="/rest/config/running/interface/TenGigabitEthernet/%22101/0/10%22/switchport/mode">
  <vlan-mode>access</vlan-mode>
  <private-vlan y:self="/rest/config/running/interface/TenGigabitEthernet/%22101/0/10%22/switchport/mode/private-vlan">  # noqa
    <trunk y:self="/rest/config/running/interface/TenGigabitEthernet/%22101/0/10%22/switchport/mode/private-vlan/trunk"/>  # noqa
  </private-vlan>
</mode>
"""

MODE_RESPONSE_TRUNK = """
<mode xmlns="urn:brocade.com:mgmt:brocade-interface"
      xmlns:y="http://brocade.com/ns/rest"
      y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/18%22/switchport/mode">
  <vlan-mode>trunk</vlan-mode>
  <private-vlan y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/18%22/switchport/mode/private-vlan">  # noqa
    <trunk y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/18%22/switchport/mode/private-vlan/trunk"/>  # noqa
  </private-vlan>
</mode>
"""

TRUNK_VLAN_RESPONSE = """
<trunk xmlns="urn:brocade.com:mgmt:brocade-interface"
       xmlns:y="http://brocade.com/ns/rest"
       y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/18%22/switchport/trunk">
  <allowed y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/18%22/switchport/trunk/allowed">  # noqa
    <rspan-vlan y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/18%22/switchport/trunk/allowed/rspan-vlan"/>  # noqa
    <vlan y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/18%22/switchport/trunk/allowed/vlan">  # noqa
      <add>1,4001,4004,4025,4050</add>
    </vlan>
  </allowed>
  <tag y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/18%22/switchport/trunk/tag">  # noqa
    <native-vlan>true</native-vlan>
  </tag>
</trunk>
"""

ACCESS_VLAN_RESPONSE = """
<access xmlns="urn:brocade.com:mgmt:brocade-interface"
        xmlns:y="http://brocade.com/ns/rest"
        y:self="/rest/config/running/interface/TenGigabitEthernet/%22101/0/10%22/switchport/access">  # noqa
  <vlan>10</vlan>
</access>
"""

TRUNK_NATIVE_VLAN_RESPONSE_NO_VLANS = """
<trunk xmlns="urn:brocade.com:mgmt:brocade-interface"
       xmlns:y="http://brocade.com/ns/rest"
       y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/10%22/switchport/trunk">
  <allowed y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/10%22/switchport/trunk/allowed">  # noqa
    <rspan-vlan y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/10%22/switchport/trunk/allowed/rspan-vlan"/>  # noqa
    <vlan y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/10%22/switchport/trunk/allowed/vlan"/>  # noqa
  </allowed>
  <tag y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/10%22/switchport/trunk/tag">  # noqa
    <native-vlan>true</native-vlan>
  </tag>
  <native-vlan>10</native-vlan>
</trunk>
"""

TRUNK_NATIVE_VLAN_RESPONSE_WITH_VLANS = """
<trunk xmlns="urn:brocade.com:mgmt:brocade-interface"
       xmlns:y="http://brocade.com/ns/rest"
       y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/10%22/switchport/trunk">
  <allowed y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/10%22/switchport/trunk/allowed">  # noqa
    <rspan-vlan y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/10%22/switchport/trunk/allowed/rspan-vlan"/>  # noqa
    <vlan y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/10%22/switchport/trunk/allowed/vlan">  # noqa
      <add>4001,4025</add>
    </vlan>
  </allowed>
  <tag y:self="/rest/config/running/interface/TenGigabitEthernet/%22104/0/10%22/switchport/trunk/tag">  # noqa
    <native-vlan>true</native-vlan>
  </tag>
  <native-vlan>10</native-vlan>
</trunk>
"""

SWITCHPORT_PAYLOAD = '<switchport></switchport>'

TRUNK_PAYLOAD = '<mode><vlan-mode>trunk</vlan-mode></mode>'

TRUNK_NATIVE_PAYLOAD = '<trunk><native-vlan>102</native-vlan></trunk>'

TRUNK_VLAN_PAYLOAD = '<vlan><add>102</vlan></vlan>'

TRUNK_REMOVE_VLAN_PAYLOAD = '<vlan><remove>102</remove></vlan>'

INTERFACE1 = '104/0/10'
INTERFACE2 = '104/0/18'
INTERFACE3 = '104/0/20'


class TestBrocade(object):
    """ Unit tests for the Brocade driver.

    The tests use the requests_mock library to return prerecorded responses
    from the switch (without any actual communication with the switch
    happening during the tests), or check that the correct payload was sent
    to the switch, at the right url.

    Inside the `requests_mock.mock()` context, every call made with the
    requests library will be directed to the mock object. We then register the
    urls we want to mock, and what to return when they are requested. An
    exception will be thrown if a request goes to a non-registered url.

    Example below will return the PRERECORDER_RESPONSE string.
    ```
    with requests_mock.mock() as mock:
        # Register the url and the text we want to return on a get
        # request to it
        mock.get(url, text=PRERECORDED_RESPONSE)
        r = requests.get(url)
    ```
    """

    @pytest.fixture()
    def switch(self):
        """Create a brocade Switch object to work with."""
        from hil.ext.switches import brocade
        return brocade.Brocade(
            label='theSwitch',
            hostname='http://example.com',
            username='admin',
            password='admin',
            interface_type='TenGigabitEthernet'
        ).session()

    @pytest.fixture()
    def nic(self):
        """Create a Nic object (and associated Node) to work with."""
        from hil.ext.obm.ipmi import Ipmi
        return model.Nic(
            model.Node(
                label='node-99',
                obm=Ipmi(
                    type="http://schema.massopencloud.org/haas/v0/obm/ipmi",
                    host="ipmihost",
                    user="root",
                    password="tapeworm")),
            'ipmi',
            '00:11:22:33:44:55')

    @pytest.fixture
    def network(self):
        """Create a network object (and associated project) to work with."""
        project = model.Project('anvil-nextgen')
        return model.Network(project, [project], True, '102', 'hammernet')

    def test_get_port_networks(self, switch):
        """Test the get_port_networks method"""
        with requests_mock.mock() as mock:

            PORT1 = model.Port(label=INTERFACE1, switch=switch)
            PORT2 = model.Port(label=INTERFACE2, switch=switch)
            PORT3 = model.Port(label=INTERFACE3, switch=switch)

            mock.get(switch._construct_url(INTERFACE1, suffix='trunk'),
                     text=TRUNK_NATIVE_VLAN_RESPONSE_WITH_VLANS)
            mock.get(switch._construct_url(INTERFACE2, suffix='trunk'),
                     text=TRUNK_NATIVE_VLAN_RESPONSE_NO_VLANS)
            mock.get(switch._construct_url(INTERFACE3, suffix='trunk'),
                     text=TRUNK_VLAN_RESPONSE)
            response = switch.get_port_networks([PORT1,
                                                 PORT2,
                                                 PORT3])
            assert response == {
                PORT1: [('vlan/native', '10'),
                        ('vlan/4001', '4001'),
                        ('vlan/4025', '4025')],
                PORT2: [('vlan/native', '10')],
                PORT3: [('vlan/1', '1'),
                        ('vlan/4001', '4001'),
                        ('vlan/4004', '4004'),
                        ('vlan/4025', '4025'),
                        ('vlan/4050', '4050')]
            }

    def test_get_mode(self, switch):
        """Test the _get_mode helper method"""
        with requests_mock.mock() as mock:
            mock.get(switch._construct_url(INTERFACE1, suffix='mode'),
                     text=MODE_RESPONSE_ACCESS)
            response = switch._get_mode(INTERFACE1)
            assert response == 'access'

            mock.get(switch._construct_url(INTERFACE1, suffix='mode'),
                     text=MODE_RESPONSE_TRUNK)
            response = switch._get_mode(INTERFACE1)
            assert response == 'trunk'

    def test_modify_port(self, switch, nic, network):
        """Test the modify_port method"""
        # Create a port on the switch and connect it to the nic
        port = model.Port(label=INTERFACE1, switch=switch)
        port.nic = nic

        # Test action to set a network as native
        action_native = model.NetworkingAction(type='modify_port',
                                               nic=nic,
                                               new_network=network,
                                               channel='vlan/native')

        with requests_mock.mock() as mock:
            url_switch = switch._construct_url(INTERFACE1)
            mock.post(url_switch)
            url_mode = switch._construct_url(INTERFACE1, suffix='mode')
            mock.put(url_mode)
            url_tag = switch._construct_url(INTERFACE1,
                                            suffix='trunk/tag/native-vlan')
            mock.delete(url_tag)
            url_trunk = switch._construct_url(INTERFACE1, suffix='trunk')
            mock.put(url_trunk)

            switch.modify_port(action_native.nic.port.label,
                               action_native.channel,
                               action_native.new_network.network_id)

            assert mock.called
            assert mock.call_count == 4
            assert mock.request_history[0].text == SWITCHPORT_PAYLOAD
            assert mock.request_history[1].text == TRUNK_PAYLOAD
            assert mock.request_history[3].text == TRUNK_NATIVE_PAYLOAD

        # Test action to remove a native network
        action_rm_native = model.NetworkingAction(type='modify_port',
                                                  nic=nic,
                                                  new_network=None,
                                                  channel='vlan/native')

        with requests_mock.mock() as mock:
            url_native = switch._construct_url(INTERFACE1,
                                               suffix='trunk/native-vlan')
            mock.delete(url_native)

            switch.modify_port(action_rm_native.nic.port.label,
                               action_rm_native.channel,
                               None)

            assert mock.called
            assert mock.call_count == 1

        # Test action to add a vlan
        action_vlan = model.NetworkingAction(type='modify_port',
                                             nic=nic,
                                             new_network=network,
                                             channel='vlan/102')
        with requests_mock.mock() as mock:
            url_switch = switch._construct_url(INTERFACE1)
            mock.post(url_switch)
            url_mode = switch._construct_url(INTERFACE1,
                                             suffix='mode')
            mock.put(url_mode)
            url_trunk = switch._construct_url(INTERFACE1,
                                              suffix='trunk/allowed/vlan')
            mock.put(url_trunk)

            switch.modify_port(action_vlan.nic.port.label,
                               action_vlan.channel,
                               action_vlan.new_network.network_id)

            assert mock.called
            assert mock.call_count == 3
            assert mock.request_history[0].text == SWITCHPORT_PAYLOAD
            assert mock.request_history[1].text == TRUNK_PAYLOAD
            assert mock.request_history[2].text == TRUNK_VLAN_PAYLOAD

        # Test action to remove a vlan
        action_rm_vlan = model.NetworkingAction(type='modify_port',
                                                nic=nic,
                                                new_network=None,
                                                channel='vlan/102')
        with requests_mock.mock() as mock:
            url_trunk = switch._construct_url(INTERFACE1,
                                              suffix='trunk/allowed/vlan')
            mock.put(url_trunk)

            switch.modify_port(action_rm_vlan.nic.port.label,
                               action_rm_vlan.channel,
                               None)

            assert mock.called
            assert mock.call_count == 1
            assert mock.request_history[0].text == TRUNK_REMOVE_VLAN_PAYLOAD

    def test_construct_url(self, switch):
        """Test the _construct_url helper method"""
        assert switch._construct_url('1/0/4') == (
            'http://example.com/rest/config/running/interface/'
            'TenGigabitEthernet/%221/0/4%22'
        )

        assert switch._construct_url('1/0/4', suffix='mode') == (
            'http://example.com/rest/config/running/interface/'
            'TenGigabitEthernet/%221/0/4%22/switchport/mode'
        )
