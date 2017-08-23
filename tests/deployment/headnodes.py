# Copyright 2013-2015 Massachusetts Open Cloud Contributors
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
"""Unit tests for headnodes.

These require an actual libvirt daemon (and full HIL setup), and are
somewhat particular to the MOC's development environment. They may be
difficult to run in other contexts.
"""

import json

from hil.test_common import config_testsuite, fail_on_log_warnings, \
    fresh_database, with_request_context, headnode_cleanup, \
    network_create_simple, server_init
from hil.dev_support import have_dry_run
from hil import config, api
import pytest


@pytest.fixture
def configure():
    """Configure HIL"""
    config_testsuite()
    config.load_extensions()


fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)
fresh_database = pytest.fixture(fresh_database)
server_init = pytest.fixture(server_init)


with_request_context = pytest.yield_fixture(with_request_context)


headnode_cleanup = pytest.fixture(headnode_cleanup)
pytestmark = pytest.mark.usefixtures('configure',
                                     'server_init',
                                     'fresh_database',
                                     'with_request_context',
                                     'headnode_cleanup')


class TestHeadNode:
    """Headnode related deployment tests."""

    def test_headnode(self):
        """Test each of the headnode related operations

        * create
        * connect_hnic,
        * connect_network
        * start
        * stop
        * delete
        """
        api.project_create('anvil-nextgen')
        network_create_simple('spider-web', 'anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hnic-0')
        api.headnode_connect_network('hn-0', 'hnic-0', 'spider-web')
        if have_dry_run():
            pytest.xfail("Running in dry-run mode; can't talk to libvirt.")
        assert json.loads(api.show_headnode('hn-0'))['vncport'] is None
        api.headnode_start('hn-0')
        assert json.loads(api.show_headnode('hn-0'))['vncport'] is not None
        api.headnode_stop('hn-0')
        api.headnode_delete('hn-0')

    def test_headnode_deletion_while_running(self):
        """Test deleting a headnode while it's running."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode-2')
        api.headnode_start('hn-0')
        api.headnode_delete('hn-0')
