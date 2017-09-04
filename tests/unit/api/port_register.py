# Copyright 2013-2017 Massachusetts Open Cloud Contributors
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

"""Unit tests for port_register"""
from hil import api, errors
from hil.test_common import config_testsuite, config_merge, config, \
    fail_on_log_warnings, with_request_context, fresh_database, server_init
import pytest

BROCADE = 'http://schema.massopencloud.org/haas/v0/switches/brocade'
DELL = 'http://schema.massopencloud.org/haas/v0/switches/powerconnect55xx'
NEXUS = 'http://schema.massopencloud.org/haas/v0/switches/nexus'


@pytest.fixture
def configure():
    """Configure HIL"""
    config_testsuite()
    config_merge({
        'extensions': {
            'hil.ext.switches.brocade': '',
            'hil.ext.switches.dell': '',
            'hil.ext.switches.nexus': '',
        },
    })
    config.load_extensions()


fresh_database = pytest.fixture(fresh_database)
fail_on_log_warnings = pytest.fixture(fail_on_log_warnings)
server_init = pytest.fixture(server_init)
with_request_context = pytest.yield_fixture(with_request_context)

default_fixtures = ['fail_on_log_warnings',
                    'configure',
                    'fresh_database',
                    'server_init',
                    'with_request_context']

pytestmark = pytest.mark.usefixtures(*default_fixtures)


class TestPortValidate:
    """Test port_register with invalid port names for various switches."""

    def test_register_port_invalid_name_brocade(self):
        """Registering a port with an invalid name should fail"""

        api.switch_register('brocade', type=BROCADE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname",
                            interface_type="Tengigabitethernet")

        # test some random invalid port names for brocade switch
        with pytest.raises(errors.BadArgumentError):
            api.switch_register_port('brocade', 'blah-blah')

        with pytest.raises(errors.BadArgumentError):
            api.switch_register_port('brocade', '1/q/1')

        with pytest.raises(errors.BadArgumentError):
            api.switch_register_port('brocade', '1/12/32q')

        # register some valid port names
        api.switch_register_port('brocade', '1/0/12')
        api.switch_register_port('brocade', '1/12')

    def test_register_port_invalid_name_nexus(self):
        """Registering a port with an invalid name should fail"""

        api.switch_register('nexus', type=NEXUS,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname",
                            dummy_vlan=2222)

        # test some random invalid port names for cisco nexus
        with pytest.raises(errors.BadArgumentError):
            api.switch_register_port('nexus', 'blah-blah')

        with pytest.raises(errors.BadArgumentError):
            api.switch_register_port('nexus', 'eethernet1/2')

        with pytest.raises(errors.BadArgumentError):
            api.switch_register_port('nexus', 'Ethernet1')

        with pytest.raises(errors.BadArgumentError):
            api.switch_register_port('nexus', 'Ethernet/12')

        # register some valid port names
        api.switch_register_port('nexus', 'Ethernet1/8')
        api.switch_register_port('nexus', 'Ethernet1/0/1')
        api.switch_register_port('nexus', 'ethernet1/2')

    def test_register_port_invalid_name_dell(self):
        """Registering a port with an invalid name should fail"""

        api.switch_register('dell', type=DELL,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")

        # test some random invalid port names for both delll switches
        with pytest.raises(errors.BadArgumentError):
            api.switch_register_port('dell', 'blah-blah')

        with pytest.raises(errors.BadArgumentError):
            api.switch_register_port('dell', 'gi1/0/1q')

        with pytest.raises(errors.BadArgumentError):
            api.switch_register_port('dell', 'gi/0/1')

        # register some valid port names
        api.switch_register_port('dell', 'gi1/0/1')
        api.switch_register_port('dell', 'te1/0/1')
        api.switch_register_port('dell', 'gi2/1')
        api.switch_register_port('dell', 'te1/12')
