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

from haas.drivers.null_vlan import *

def vlan_test(vlan_list):
    """A decorator for tests of the vlan helper file.  Pass in a string for
    the vlan_list configuration option, which determines which vlans can be
    used for networking.
    """

    def dec(f):
        def config_initialize():
            testsuite_config()
            config_merge({
                'general': {
                    'driver': 'null_vlan',
                },
                'vlan': {
                    'vlans': vlan_list,
                },
            })

        @wraps(f)
        def wrapped(self):
            config_clear()
            config_initialize()
            db = newDB()
            f(self, db)
            releaseDB(db)

        return wrapped

    return dec


class TestInit_DB:
    """Tests init_db."""

    @vlan_test('100-109')
    def test_init_db_1(self, db):
        pass

    @vlan_test('1-10,40-100, 4044, 3000-4000')
    def test_init_db_2(self, db):
        pass


class TestNetworkID:
    """Tests allocation and freeing of network IDs"""

    @vlan_test('84')
    def test_allocate_free_1(self, db):
        assert '84' == get_new_network_id(db)
        assert None == get_new_network_id(db)
        free_network_id(db, '84')
        assert '84' == get_new_network_id(db)
        assert None == get_new_network_id(db)

    @vlan_test('84, 85')
    def test_allocate_free_2(self, db):
        get_new_network_id(db)
        get_new_network_id(db)
        free_network_id(db, '84')
        assert '84' == get_new_network_id(db)
        free_network_id(db, '85')
        assert '85' == get_new_network_id(db)

    @vlan_test('84')
    def test_free_nonexist(self,db):
        # This test ensures that attempting to free a vlan that is not in the
        # db is handled gracefully, and the program does not crash.
        # TODO: Check to see that an error message is actually logged.
        free_network_id(db, '85')
