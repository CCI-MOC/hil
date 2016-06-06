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

"""Unit tests for api.py"""
import haas
from haas import model, api, deferred, server, config
from haas.model import db
from haas.test_common import *
from haas.network_allocator import get_network_allocator
import pytest
import json

import requests
import os
import subprocess
from urlparse import urljoin
from requests.exceptions import ConnectionError
from haas.client_lib.client_lib import hilClientLib

MOCK_SWITCH_TYPE = 'http://schema.massopencloud.org/haas/v0/switches/mock'
OBM_TYPE_MOCK = 'http://schema.massopencloud.org/haas/v0/obm/mock'
OBM_TYPE_IPMI = 'http://schema.massopencloud.org/haas/v0/obm/ipmi'

HAAS_ENDPOINT="http://127.0.0.1"
HAAS_USERNAME="hil_user"
HAAS_PASSWORD="hil_pass1234"
h = hilClientLib(HAAS_ENDPOINT, HAAS_USERNAME, HAAS_PASSWORD)  #Instantiating the client library.


@pytest.fixture
def configure():
    config_testsuite()
    config_merge({
        'extensions': {
            'haas.ext.switches.mock': '',
            'haas.ext.obm.ipmi': '',
            'haas.ext.obm.mock': '',
        },
    })
    config.load_extensions()


fresh_database = pytest.fixture(fresh_database)


@pytest.fixture
def server_init():
    server.register_drivers()
    server.validate_state()


with_request_context = pytest.yield_fixture(with_request_context)


pytestmark = pytest.mark.usefixtures('configure',
                                     'fresh_database',
                                     'server_init',
                                     'with_request_context')




class Test_hilClientlib:
    """Tests if the hil client library object instantiates correctly"""

    HAAS_ENDPOINT="http://127.0.0.1"
    HAAS_USERNAME="hil_user"
    HAAS_PASSWORD="hil_pass1234"

    def create_env(self):
        """ source required parameters in the environment """
        with open("/tmp/hil_env", 'w') as f:
            f.write("export HAAS_ENDPOINT=up_the_HIL; export HAAS_USERNAME=jack; export HAAS_PASSWORD=broke_his_crown\n")
        command = ['bash', '-c', 'source /tmp/hil_env && env']
        proc = subprocess.Popen(command, stdout = subprocess.PIPE)

        for line in proc.stdout:
            (key, _, value) = line.partition("=")
            if key in ['HAAS_ENDPOINT', 'HAAS_USERNAME', 'HAAS_PASSWORD']:
                value = value.strip('\n')
                os.environ[key] = value


    def test_parameter_passing(self):
        h = hilClientLib(HAAS_ENDPOINT, HAAS_USERNAME, HAAS_PASSWORD)  #Instantiating the client library.
        assert h.endpoint == self.HAAS_ENDPOINT
        assert h.user == self.HAAS_USERNAME
        assert h.password == self.HAAS_PASSWORD

    def test_env_parameter_passing(self):
        self.create_env()
        h = hilClientLib() #Instantiating client library with values from user env.
        assert h.endpoint == "up_the_HIL"
        assert h.user == "jack"
        assert h.password == "broke_his_crown"





class TestQuery:
    """test the query api"""

    def _compare_node_dumps(self, actual, expected):
        """This is a helper method which compares the parsed json output of
        two show_headnode calls for equality. There are a couple issue to work
        around to get an accurate result - in particular, we often don't care
        about the order of lists, which needs special handling (especially when
        the arguments aren't orderable).
        """
        # For two lists to be equal, their elements have to be in the same
        # order. However, there is no ordering defined on dictionaries, so we
        # can't just sort the lists. instead we check our desired notion of
        # equality manually, and then clear both hnic lists before comparing
        # the rest of the data:
        for nic in actual['nics']:
            assert nic in expected['nics']
            expected['nics'].remove(nic)
        assert len(expected['nics']) == 0
        actual['nics'] = []
        assert expected == actual

    def test_free_nodes(self):
        api.node_register('master-control-program', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('robocop', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('data', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        result = json.loads(api.list_free_nodes())
        # For the lists to be equal, the ordering must be the same:
        result.sort()
        assert result == [
            'data',
            'master-control-program',
            'robocop',
        ]

    def test_list_projects(self):
        assert json.loads(api.list_projects()) == []
        api.project_create('anvil-nextgen')
        assert json.loads(api.list_projects()) == ['anvil-nextgen']
        api.project_create('runway')
        api.project_create('manhattan')
        assert sorted(json.loads(api.list_projects())) == [
            'anvil-nextgen',
            'manhattan',
            'runway',
        ]

    def test_no_free_nodes(self):
        assert json.loads(api.list_free_nodes()) == []

    def test_some_non_free_nodes(self):
        """Make sure that allocated nodes don't show up in the free list."""
        api.node_register('master-control-program', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('robocop', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('data', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'robocop')
        api.project_connect_node('anvil-nextgen', 'data')

        assert json.loads(api.list_free_nodes()) == ['master-control-program']

    def test_show_node(self):
        """Test the show_node api call.

        We create a node, and query it twice: once before it is reserved,
        and once after it has been reserved by a project and attached to
        a network. Two things should change: (1) "project" should show registered project,
        and (2) the newly attached network should be listed.
        """
        api.node_register('robocop', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('robocop', 'eth0', 'DE:AD:BE:EF:20:14')
        api.node_register_nic('robocop', 'wlan0', 'DE:AD:BE:EF:20:15')

        actual = json.loads(api.show_node('robocop'))
        expected = {
            'name': 'robocop',
            'project': None,
            'nics': [
                {
                    'label':'eth0',
                    'macaddr': 'DE:AD:BE:EF:20:14',
                    "networks": {}
                },
                {
                    'label':'wlan0',
                    'macaddr': 'DE:AD:BE:EF:20:15',
                    "networks": {}
                }
            ],
        }
        self._compare_node_dumps(actual, expected)

    def test_show_node(self):
        """Test the show_node api call.
        We create a node, and query it twice: once before it is reserved,
        and once after it has been reserved by a project and attached to
        a network. Two things should change: (1) "project" should show registered project,
        and (2) the newly attached network should be listed.
        """

    def test_show_node_unavailable(self):
        api.node_register('robocop', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('robocop', 'eth0', 'DE:AD:BE:EF:20:14')
        api.node_register_nic('robocop', 'wlan0', 'DE:AD:BE:EF:20:15')

        actual = json.loads(api.show_node('robocop'))
        expected = {
            'name': 'robocop',
            'project': None,
            'nics': [
                {
                    'label':'eth0',
                    'macaddr': 'DE:AD:BE:EF:20:14',
                    "networks": {}
                },
                {
                    'label':'wlan0',
                    'macaddr': 'DE:AD:BE:EF:20:15',
                    "networks": {}
                }
            ],
        }
        self._compare_node_dumps(actual, expected)

    def test_show_node_multiple_network(self):
        api.node_register('robocop', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('robocop', 'eth0', 'DE:AD:BE:EF:20:14')
        api.node_register_nic('robocop', 'wlan0', 'DE:AD:BE:EF:20:15')

        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'robocop')
        network_create_simple('pxe', 'anvil-nextgen')
        api.node_connect_network('robocop', 'eth0', 'pxe')
        network_create_simple('storage', 'anvil-nextgen')
        api.node_connect_network('robocop', 'wlan0', 'storage')
        deferred.apply_networking()

        actual = json.loads(api.show_node('robocop'))
        expected = {
            'name': 'robocop',
            'project':'anvil-nextgen',
            'nics': [
                {
                    'label': 'eth0',
                    'macaddr': 'DE:AD:BE:EF:20:14',
                    "networks": {
                        get_network_allocator().get_default_channel(): 'pxe'
                    }
                },
                {
                    'label': 'wlan0',
                    'macaddr': 'DE:AD:BE:EF:20:15',
                    "networks": {
                        get_network_allocator().get_default_channel(): 'storage'
                    }
                }
            ],
        }
        self._compare_node_dumps(actual, expected)

    def test_show_nonexistant_node(self):
        with pytest.raises(api.NotFoundError):
            api.show_node('master-control-program')

    def test_project_nodes_exist(self):
        api.node_register('master-control-program', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('robocop', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('data', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'master-control-program')
        api.project_connect_node('anvil-nextgen', 'robocop')
        api.project_connect_node('anvil-nextgen', 'data')
        result = json.loads(api.list_project_nodes('anvil-nextgen'))
        # For the lists to be equal, the ordering must be the same:
        result.sort()
        assert result == [
            'data',
            'master-control-program',
            'robocop',
        ]

    def test_project_headnodes_exist(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create('hn1', 'anvil-nextgen', 'base-headnode')
        api.headnode_create('hn2', 'anvil-nextgen', 'base-headnode')

        result = json.loads(api.list_project_headnodes('anvil-nextgen'))
        # For the lists to be equal, the ordering must be the same:
        result.sort()
        assert result == [
            'hn0',
            'hn1',
            'hn2',
        ]

    def test_no_project_nodes(self):
        api.project_create('anvil-nextgen')
        assert json.loads(api.list_project_nodes('anvil-nextgen')) == []

    def test_no_project_headnodes(self):
        api.project_create('anvil-nextgen')
        assert json.loads(api.list_project_headnodes('anvil-nextgen')) == []

    def test_some_nodes_in_project(self):
        """Test that only assigned nodes are in the project."""
        api.node_register('master-control-program', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('robocop', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('data', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'robocop')
        api.project_connect_node('anvil-nextgen', 'data')

        result = json.loads(api.list_project_nodes('anvil-nextgen'))
        result.sort()
        assert result == ['data', 'robocop']

    def test_project_list_networks(self):
        api.project_create('anvil-nextgen')

        network_create_simple('pxe', 'anvil-nextgen')
        network_create_simple('public', 'anvil-nextgen')
        network_create_simple('private', 'anvil-nextgen')

        result = json.loads(api.list_project_networks('anvil-nextgen'))
        # For the lists to be equal, the ordering must be the same:
        result.sort()
        assert result == [
                'private',
                'public',
                'pxe'
        ]

    def test_no_project_networks(self):
        api.project_create('anvil-nextgen')
        assert json.loads(api.list_project_nodes('anvil-nextgen')) == []

    import uuid

    def test_show_headnode(self):
        api.project_create('anvil-nextgen')
        network_create_simple('spiderwebs', 'anvil-nextgen')
        api.headnode_create('BGH', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('BGH', 'eth0')
        api.headnode_create_hnic('BGH', 'wlan0')
        api.headnode_connect_network('BGH', 'eth0', 'spiderwebs')


        result = json.loads(api.show_headnode('BGH'))

        # Verify UUID is well formed, then delete it, since we can't match it
        # exactly in the check below
        temp = uuid.UUID(result['uuid'])
        del result['uuid']

        # For the lists to be equal, the ordering must be the same:
        result['hnics'].sort()
        assert result == {
            'name':     'BGH',
            'project':  'anvil-nextgen',
            'base_img': 'base-headnode',
            'hnics': [
                'eth0',
                'wlan0',
            ],
            'vncport': None
        }

    def test_show_nonexistant_headnode(self):
        with pytest.raises(api.NotFoundError):
            api.show_headnode('BGH')


    def test_list_headnode_images(self):
        result = json.loads(api.list_headnode_images())
        assert result == [ 'base-headnode', 'img1', 'img2', 'img3', 'img4' ]


class Test_show_network:
    """Test the show_network api cal."""

    def test_show_network_simple(self):
        api.project_create('anvil-nextgen')
        network_create_simple('spiderwebs', 'anvil-nextgen')

        result = json.loads(api.show_network('spiderwebs'))
        assert result == {
            'name': 'spiderwebs',
            'creator': 'anvil-nextgen',
            'access': 'anvil-nextgen',
            "channels": ["null"]
        }

    def test_show_network_public(self):
        api.network_create('public-network',
                           creator='admin',
                           access='',
                           net_id='432')

        result = json.loads(api.show_network('public-network'))
        assert result == {
            'name': 'public-network',
            'creator': 'admin',
            'channels': ['null'],
        }

    def test_show_network_provider(self):
        api.project_create('anvil-nextgen')
        api.network_create('spiderwebs',
                           creator='admin',
                           access='anvil-nextgen',
                           net_id='451')

        result = json.loads(api.show_network('spiderwebs'))
        assert result == {
            'name': 'spiderwebs',
            'creator': 'admin',
            'access': 'anvil-nextgen',
            'channels': ['null'],
        }




