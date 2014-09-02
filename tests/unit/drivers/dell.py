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

"""Unit tests for drivers/dell.py"""

from functools import wraps

from haas import model, api
from haas.test_common import *
import pytest

from haas.config import cfg
from haas.drivers.dell import *


def dell_backend(vlan_list):
    """A decorator for tests running on the Dell backend.  Pass in a string
    for the vlan_list configuration option, which determines which vlans can
    be used for networking.
    """

    def dec(f):
        def config_initialize():
            # Use the 'dell' backend for these tests
            cfg.add_section('general')
            cfg.set('general', 'active_switch', 'dell')
            cfg.add_section('switch dell')
            cfg.set('switch dell', 'vlans', vlan_list)

        @wraps(f)
        @clear_configuration
        def wrapped(self):
            config_initialize()
            db = newDB()
            f(self, db)
            releaseDB(db)

        return wrapped

    return dec


class TestInit_DB:
    """Tests init_db."""

    @dell_backend('100-109')
    def test_init_db_1(self, db):
        pass

    @dell_backend('1-10,40-100, 4044, 3000-4000')
    def test_init_db_2(self, db):
        pass


class TestNetworkID:
    """Tests allocation and freeing of network IDs"""

    @dell_backend('84')
    def test_allocate_free_1(self, db):
        assert '84' == get_new_network_id(db)
        assert None == get_new_network_id(db)
        free_network_id(db, '84')
        assert '84' == get_new_network_id(db)
        assert None == get_new_network_id(db)

    @dell_backend('84, 85')
    def test_allocate_free_2(self, db):
        get_new_network_id(db)
        get_new_network_id(db)
        free_network_id(db, '84')
        assert '84' == get_new_network_id(db)
        free_network_id(db, '85')
        assert '85' == get_new_network_id(db)

    @dell_backend('84')
    def test_free_nonexist(self,db):
        get_new_network_id(db)
        free_network_id(db, '84')
        with pytest.raises(api.NotFoundError):
            free_network_id(db, '85') 
