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

"""Deployment tests re: switch configuration.

For guidance on running these tests, see the section on deployment tests
in docs/testing.md.
"""


from hil import api, model, deferred
from hil.test_common import config, config_testsuite, fresh_database, \
    fail_on_log_warnings, with_request_context, site_layout, config_merge, \
    NetworkTest, network_create_simple, server_init

import pytest
import json

DELL5500 = 'http://schema.massopencloud.org/haas/v0/switches/powerconnect55xx'
NEXUS = 'http://schema.massopencloud.org/haas/v0/switches/nexus'
DELLN3000 = 'http://schema.massopencloud.org/haas/v0/switches/delln3000'


@pytest.fixture
def configure():
    """Confgure HIL."""
    config_testsuite()
    config_merge({
        'hil.ext.switches.dell': {
            'save': 'True'
         },
        'hil.ext.switches.nexus': {
            'save': 'True'
        }
    })
    config.load_extensions()


fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)
fresh_database = pytest.fixture(fresh_database)
server_init = pytest.fixture(server_init)


with_request_context = pytest.yield_fixture(with_request_context)

site_layout = pytest.fixture(site_layout)

pytestmark = pytest.mark.usefixtures('configure',
                                     'server_init',
                                     'fresh_database',
                                     'with_request_context',
                                     'site_layout')


@pytest.fixture
def not_dell_or_nexus():
    """open the site-layout file to see if we don't have a dell or cisco nexus
    switch"""

    with open('site-layout.json') as layout_data:
        layout = json.load(layout_data)
    switch_type = layout['switches'][0]['type']
    return (switch_type != NEXUS and switch_type != DELL5500 and
            switch_type != DELLN3000)


@pytest.mark.skipif(not_dell_or_nexus(),
                    reason="Skipping because not a dell or cisco switch")
class TestSwitchSavingToFlash(NetworkTest):
    """ saves the running config to the flash memory. Test is only for the dell
        switch"""

    def get_config(self, config_type):
        """returns the switch configuration file"""

        switch = model.Switch.query.one()
        session = switch.session()
        config = session._get_config(config_type)
        session.disconnect()
        return config

    def test_saving_config_file(self):
        """Test saving the switch config to flash."""
        api.project_create('anvil-nextgen')
        nodes = self.collect_nodes()

        # Create two networks
        network_create_simple('net-0', 'anvil-nextgen')
        network_create_simple('net-1', 'anvil-nextgen')

        # save the old startup config before performing a networking action
        old_startup_config = self.get_config('startup')
        # Connect n0 and n1 to net-0 and net-1 respectively
        api.node_connect_network(nodes[0].label,
                                 nodes[0].nics[0].label,
                                 'net-0')

        api.node_connect_network(nodes[1].label,
                                 nodes[1].nics[0].label,
                                 'net-1')

        deferred.apply_networking()

        # get the running config, and the new startup config
        running_config = self.get_config('running')
        new_startup_config = self.get_config('startup')

        assert new_startup_config == running_config
        assert new_startup_config != old_startup_config

        # cleanup
        api.node_detach_network(nodes[0].label,
                                nodes[0].nics[0].label,
                                'net-0')

        api.node_detach_network(nodes[1].label,
                                nodes[1].nics[0].label,
                                'net-1')

        deferred.apply_networking()
