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

from haas.test_common import *
import pytest

from haas.config import cfg, load_extensions

from haas.drivers.complex_vlan import apply_networking, get_switch_vlans
from haas.drivers.switches.test import reinitialize

def vlan_test(vlan_list):
    """A decorator for tests of the complex_vlan driver.  Pass in a string for
    the vlan_list configuration option, which determines which vlans can be
    used for networking.
    """

    def dec(f):
        def config_initialize():
            # Use the complex vlan driver for these tests
            testsuite_config()
            config_merge({
                'general': {
                    'driver': 'complex_vlan',
                },
                'vlan': {
                    'vlans': vlan_list,
                },
                'driver complex_vlan': {
                    'switch': json.dumps([
                        {'name': '0', 'switch':'test'},
                        {'name': '1', 'switch':'test'},
                        {'name': '2', 'switch':'test'},
                    ]),
                    'trunk_ports': '[]',
                },
            })
            load_extensions()

        @wraps(f)
        def wrapped(self):
            config_clear()
            config_initialize()
            db = newDB()
            reinitialize()
            f(self, db)
            releaseDB(db)

        return wrapped

    return dec

class TestApply:
    """Tests network_apply"""

    @vlan_test('84, 85')
    def test_network_apply_complex(self, db):
        """Test switch dispatch logic.

        Make two apply_networking calls, then use get_switch_vlans to check
        that the correct changes were routed to the correct underlying
        switches.
        """
        apply_networking({"1::1": '84', "1::2": '84', "2::1": '84'})
        switch_vlans = get_switch_vlans(['84', '85'])
        assert sorted(switch_vlans['84']) == sorted(["1::1", "1::2", "2::1"])
        assert switch_vlans['85'] == []

        apply_networking({"1::2": '85', "2::1": None, "0::2": '85'})
        switch_vlans = get_switch_vlans(['84', '85'])
        assert switch_vlans['84'] == ["1::1"]
        assert sorted(switch_vlans['85']) == sorted(["1::2", "0::2"])
