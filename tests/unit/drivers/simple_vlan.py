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
from haas.config import load_extensions
import pytest

from haas.drivers.simple_vlan import *

#from haas.drivers.switches.test import reinitialize
pytestmark = pytest.mark.xfail

def vlan_test(vlan_list):
    """A decorator for tests of the simple_vlan driver.  Pass in a string for
    the vlan_list configuration option, which determines which vlans can be
    used for networking.
    """

    def dec(f):
        def config_initialize():
            # Use the 'dell' backend for these tests
            testsuite_config()
            config_merge({
                'general': {
                    'driver': 'simple_vlan',
                },
                'vlan': {
                    'vlans': vlan_list,
                },
                'driver simple_vlan': {
                    'switch': json.dumps({
                        'name': '1',
                        'switch': 'test',
                    }),
                    'trunk_port': 'unused',
                },
            })
            load_extensions()

        @wraps(f)
        def wrapped(self):
            config_initialize()
            db = newDB()
            reinitialize()
            f(self, db)
            releaseDB(db)

        return wrapped

    return dec

class TestSimpleVLAN:
    """Tests basic operation of Simple VLAN driver"""

    @vlan_test('84, 85')
    def test_simple_vlan_network_operations(self, db):
        """Test switch dispatch logic.

        Make two apply_networking calls, then use get_switch_vlans to check
        that the changes were routed to the underlying switch.
        """

        apply_networking({"1":'84', "2":'84', "3":'84'})
        switch_vlans = get_switch_vlans(['84', '85'])
        assert sorted(switch_vlans['84']) == sorted(["1", "2", "3"])
        assert switch_vlans['85'] == []

        apply_networking({"2":'85', "3":None, "4":'85'})
        switch_vlans = get_switch_vlans(['84', '85'])
        assert switch_vlans['84'] == ["1"]
        assert sorted(switch_vlans['85']) == sorted(["2", "4"])
