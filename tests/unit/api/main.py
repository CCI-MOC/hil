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
from haas import model, deferred, server
from haas.test_common import *
from haas.network_allocator import get_network_allocator
import pytest
import json
import uuid

MOCK_SWITCH_TYPE = 'http://schema.massopencloud.org/haas/v0/switches/mock'
OBM_TYPE_MOCK = 'http://schema.massopencloud.org/haas/v0/obm/mock'
OBM_TYPE_IPMI = 'http://schema.massopencloud.org/haas/v0/obm/ipmi'


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
additional_database = pytest.fixture(additional_db)
fail_on_log_warnings = pytest.fixture(fail_on_log_warnings)


@pytest.fixture
def server_init():
    server.register_drivers()
    server.validate_state()


with_request_context = pytest.yield_fixture(with_request_context)


@pytest.fixture
def switchinit():
    api.switch_register('sw0',
                        type=MOCK_SWITCH_TYPE,
                        username="switch_user",
                        password="switch_pass",
                        hostname="switchname")
    api.switch_register_port('sw0', '3')


default_fixtures = ['fail_on_log_warnings',
                    'configure',
                    'fresh_database',
                    'server_init',
                    'with_request_context']

pytestmark = pytest.mark.usefixtures(*default_fixtures)


class TestProjectCreateDelete:
    """Tests for the haas.api.project_* functions."""

    pytestmark = pytest.mark.usefixtures(*(default_fixtures +
                                           ['additional_database']))

    def test_project_create_success(self):
        api.project_create('anvil-nextgen')
        api._must_find(model.Project, 'anvil-nextgen')

    def test_project_create_duplicate(self):
        with pytest.raises(api.DuplicateError):
            api.project_create('manhattan')

    def test_project_delete(self):
        api.project_delete('empty-project')
        with pytest.raises(api.NotFoundError):
            api._must_find(model.Project, 'empty-project')

    def test_project_delete_nexist(self):
        with pytest.raises(api.NotFoundError):
            api.project_delete('anvil-nextgen')

    def test_project_delete_hasnode(self):
        with pytest.raises(api.BlockedError):
            api.project_delete('manhattan')

    def test_project_delete_success_nodesdeleted(self):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_detach_node('anvil-nextgen', 'node-99')
        api.project_delete('anvil-nextgen')

    def test_project_delete_hasnetwork(self):
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        with pytest.raises(api.BlockedError):
            api.project_delete('anvil-nextgen')

    def test_project_delete_success_networksdeleted(self):
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.network_delete('hammernet')
        api.project_delete('anvil-nextgen')

    def test_project_delete_hasheadnode(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-01', 'anvil-nextgen', 'base-headnode')
        with pytest.raises(api.BlockedError):
            api.project_delete('anvil-nextgen')

    def test_duplicate_project_create(self):
        api.project_create('acme-corp')
        with pytest.raises(api.DuplicateError):
            api.project_create('acme-corp')


class TestProjectAddDeleteNetwork:
    """Tests for adding and deleting a network from a project"""

    pytestmark = pytest.mark.usefixtures(*(default_fixtures +
                                           ['additional_database']))

    def test_network_grant_project_access(self):
        api.network_grant_project_access('manhattan', 'runway_pxe')
        network = api._must_find(model.Network, 'runway_pxe')
        project = api._must_find(model.Project, 'manhattan')
        assert project in network.access
        assert network in project.networks_access

    def test_network_revoke_project_access(self):
        api.network_revoke_project_access('runway', 'runway_provider')
        network = api._must_find(model.Network, 'runway_provider')
        project = api._must_find(model.Project, 'runway')
        assert project not in network.access
        assert network not in project.networks_access

    def test_network_revoke_project_access_connected_node(self):
        api.node_connect_network(
            'runway_node_0',
            'boot-nic',
            'runway_provider')
        deferred.apply_networking()

        with pytest.raises(api.BlockedError):
            api.network_revoke_project_access('runway', 'runway_provider')

    def test_project_remove_network_owner(self):
        with pytest.raises(api.BlockedError):
            api.network_revoke_project_access('runway', 'runway_pxe')


class TestNetworking:

    def test_networking_involved(self):
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        for port in '1', '2', '3':
            api.switch_register_port('sw0', port)
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

        api.node_register('node-98', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

        api.node_register('node-97', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:14')
        api.node_register_nic('node-98', 'eth0', 'DE:AD:BE:EF:20:15')
        api.node_register_nic('node-97', 'eth0', 'DE:AD:BE:EF:20:16')
        for port, node in ('1', 'node-99'), ('2', 'node-98'), ('3', 'node-97'):
            api.port_connect_nic('sw0', port, node, 'eth0')

        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_connect_node('anvil-nextgen', 'node-98')
        network_create_simple('hammernet', 'anvil-nextgen')
        network_create_simple('spiderwebs', 'anvil-nextgen')
        api.node_connect_network('node-98', 'eth0', 'hammernet')

    def test_networking_nic_no_port(self):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:14')

        api.project_create('anvil-nextgen')

        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        with pytest.raises(api.NotFoundError):
            api.node_connect_network('node-99', 'eth0', 'hammernet')


class TestProjectConnectDetachNode:

    def test_project_connect_node(self):
        api.project_create('anvil-nextgen')
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

        api.project_connect_node('anvil-nextgen', 'node-99')
        project = api._must_find(model.Project, 'anvil-nextgen')
        node = api._must_find(model.Node, 'node-99')
        assert node in project.nodes
        assert node.project is project

    def test_project_connect_node_project_nexist(self):
        """Tests that connecting a node to a nonexistent project fails"""
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        with pytest.raises(api.NotFoundError):
            api.project_connect_node('anvil-nextgen', 'node-99')

    def test_project_connect_node_node_nexist(self):
        """Tests that connecting a nonexistent node to a projcet fails"""
        api.project_create('anvil-nextgen')
        with pytest.raises(api.NotFoundError):
            api.project_connect_node('anvil-nextgen', 'node-99')

    def test_project_connect_node_node_busy(self):
        """Connecting a node which is not free to a project should fail."""
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

        api.project_create('anvil-oldtimer')
        api.project_create('anvil-nextgen')

        api.project_connect_node('anvil-oldtimer', 'node-99')
        with pytest.raises(api.BlockedError):
            api.project_connect_node('anvil-nextgen', 'node-99')

    def test_project_detach_node(self):
        api.project_create('anvil-nextgen')
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_detach_node('anvil-nextgen', 'node-99')
        project = api._must_find(model.Project, 'anvil-nextgen')
        node = api._must_find(model.Node, 'node-99')
        assert node not in project.nodes
        assert node.project is not project

    def test_project_detach_node_notattached(self):
        """Tests that removing a node from a project it's not in fails."""
        api.project_create('anvil-nextgen')
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        with pytest.raises(api.NotFoundError):
            api.project_detach_node('anvil-nextgen', 'node-99')

    def test_project_detach_node_project_nexist(self):
        """Tests that removing a node from a nonexistent project fails."""
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        with pytest.raises(api.NotFoundError):
            api.project_detach_node('anvil-nextgen', 'node-99')

    def test_project_detach_node_node_nexist(self):
        """Tests that removing a nonexistent node from a project fails."""
        api.project_create('anvil-nextgen')
        with pytest.raises(api.NotFoundError):
            api.project_detach_node('anvil-nextgen', 'node-99')

    def test_project_detach_node_on_network(self, switchinit):
        api.project_create('anvil-nextgen')
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:13')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', '3', 'node-99', 'eth0')
        api.node_connect_network('node-99', 'eth0', 'hammernet')
        with pytest.raises(api.BlockedError):
            api.project_detach_node('anvil-nextgen', 'node-99')

    def test_project_detach_node_success_nic_not_on_network(self):
        api.project_create('anvil-nextgen')
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:13')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.project_detach_node('anvil-nextgen', 'node-99')

    def test_project_detach_node_removed_from_network(self, switchinit):
        api.project_create('anvil-nextgen')
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:13')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', '3', 'node-99', 'eth0')
        api.node_connect_network('node-99', 'eth0', 'hammernet')
        deferred.apply_networking()
        api.node_detach_network('node-99', 'eth0', 'hammernet')
        deferred.apply_networking()

        api.project_detach_node('anvil-nextgen', 'node-99')


class TestRegisterCorrectObm:
    """Tests that node_register stores obm driver information into
    correct corresponding tables

    """

    def test_ipmi(self):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

        node_obj = model.Node.query.filter_by(label="compute-01")\
                        .join(model.Obm).join(haas.ext.obm.ipmi.Ipmi).first()

        # Comes from table node
        assert str(node_obj.label) == 'compute-01'
        # Comes from table obm
        assert str(node_obj.obm.api_name) == OBM_TYPE_IPMI
        # Comes from table ipmi
        assert str(node_obj.obm.host) == 'ipmihost'

    def test_mockobm(self):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/mock",
                  "host": "mockObmhost",
                  "user": "root",
                  "password": "tapeworm"})

        node_obj = model.Node.query.filter_by(label="compute-01")\
                        .join(model.Obm).join(haas.ext.obm.mock.MockObm).first()  # noqa

        # Comes from table node
        assert str(node_obj.label) == 'compute-01'
        # Comes from table obm
        assert str(node_obj.obm.api_name) == OBM_TYPE_MOCK
        # Comes from table mockobm
        assert str(node_obj.obm.host) == 'mockObmhost'


class TestNodeRegisterDelete:
    """Tests for the haas.api.node_* functions."""

    def test_node_register(self):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api._must_find(model.Node, 'node-99')

    def test_node_register_with_metadata(self):
        api.node_register('node-99',
                          obm={
                              "type": "http://schema.massopencloud.org/haas/v0"
                                      "/obm/ipmi",
                              "host": "ipmihost",
                              "user": "root",
                              "password": "tapeworm"
                          },
                          metadata={
                              "EK": "pk"
                          })
        api._must_find(model.Node, 'node-99')

    def test_node_register_JSON_metadata(self):
        api.node_register('node-99',
                          obm={
                              "type": "http://schema.massopencloud.org/haas/v0"
                                      "/obm/ipmi",
                              "host": "ipmihost",
                              "user": "root",
                              "password": "tapeworm"},
                          metadata={
                              "EK": {"val1": 1, "val2": 2}
                          })
        api._must_find(model.Node, 'node-99')

    def test_node_register_with_multiple_metadata(self):
        api.node_register('node-99',
                          obm={
                              "type": "http://schema.massopencloud.org/haas/v0"
                                      "/obm/ipmi",
                              "host": "ipmihost",
                              "user": "root",
                              "password": "tapeworm"
                          },
                          metadata={
                              "EK": "pk",
                              "SHA256": "b5962d8173c14e60259211bcf25d1263c36e0"
                              "ad7da32ba9d07b224eac1834813"
                          })
        api._must_find(model.Node, 'node-99')

    def test_duplicate_node_register(self):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        with pytest.raises(api.DuplicateError):
            api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

    def test_node_delete(self):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_delete('node-99')
        with pytest.raises(api.NotFoundError):
            api._must_find(model.Node, 'node-99')

    def test_node_delete_nexist(self):
        with pytest.raises(api.NotFoundError):
            api.node_delete('node-99')

    def test_node_delete_nic_exist(self):
        """node_delete should respond with an error if the node has nics."""
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.BlockedError):
            api.node_delete('node-99')


class TestNodeRegisterDeleteNic:

    def test_node_register_nic(self):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        nic = api._must_find(model.Nic, '01-eth0')
        assert nic.owner.label == 'compute-01'

    def test_node_register_nic_no_node(self):
        with pytest.raises(api.NotFoundError):
            api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')

    def test_node_register_nic_duplicate_nic(self):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        nic = api._must_find(model.Nic, '01-eth0')
        with pytest.raises(api.DuplicateError):
            api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:15')

    def test_node_delete_nic_success(self):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        api.node_delete_nic('compute-01', '01-eth0')
        api._assert_absent(model.Nic, '01-eth0')
        api._must_find(model.Node, 'compute-01')

    def test_node_delete_nic_nic_nexist(self):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        with pytest.raises(api.NotFoundError):
            api.node_delete_nic('compute-01', '01-eth0')

    def test_node_delete_nic_node_nexist(self):
        with pytest.raises(api.NotFoundError):
            api.node_delete_nic('compute-01', '01-eth0')

    def test_node_delete_nic_wrong_node(self):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('compute-02', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.node_delete_nic('compute-02', '01-eth0')

    def test_node_delete_nic_wrong_nexist_node(self):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.node_delete_nic('compute-02', '01-eth0')

    def test_node_register_nic_diff_nodes(self):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('compute-02', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', 'ipmi', 'DE:AD:BE:EF:20:14')
        api.node_register_nic('compute-02', 'ipmi', 'DE:AD:BE:EF:20:14')


class TestNodeRegisterDeleteMetadata:

    pytestmark = pytest.mark.usefixtures(*(default_fixtures +
                                           ['additional_database']))

    def test_node_set_metadata(self):
        api.node_set_metadata('free_node_0', 'EK', 'pk')
        metadata = api._must_find_n(api._must_find(model.Node,
                                                   'free_node_0'),
                                    model.Metadata, 'EK')
        assert metadata.owner.label == 'free_node_0'

    def test_node_update_metadata(self):
        api.node_set_metadata('runway_node_0', 'EK', 'new_pk')
        metadata = api._must_find_n(api._must_find(model.Node,
                                                   'runway_node_0'),
                                    model.Metadata, 'EK')
        assert json.loads(metadata.value) == 'new_pk'

    def test_node_set_metadata_no_node(self):
        with pytest.raises(api.NotFoundError):
            api.node_set_metadata('compute-01', 'EK', 'pk')

    def test_node_delete_metadata_success(self):
        api.node_set_metadata('free_node_0', 'EK', 'pk')
        api.node_delete_metadata('free_node_0', 'EK')
        api._assert_absent_n(api._must_find(model.Node,
                                            'free_node_0'),
                             model.Metadata, 'EK')

    def test_node_delete_metadata_metadata_nexist(self):
        with pytest.raises(api.NotFoundError):
            api.node_delete_metadata('free_node_0', 'EK')

    def test_node_delete_metadata_node_nexist(self):
        with pytest.raises(api.NotFoundError):
            api.node_delete_metadata('compute-01', 'EK')

    def test_node_delete_metadata_wrong_node(self):
        api.node_set_metadata('free_node_0', 'EK', 'pk')
        with pytest.raises(api.NotFoundError):
            api.node_delete_metadata('free_node_1', 'EK')

    def test_node_delete_metadata_wrong_nexist_node(self):
        api.node_set_metadata('free_node_0', 'EK', 'pk')
        with pytest.raises(api.NotFoundError):
            api.node_delete_metadata('compute-02', 'EK')

    def test_node_set_metadata_diff_nodes(self):
        api.node_set_metadata('free_node_0', 'EK', 'pk')
        api.node_set_metadata('free_node_1', 'EK', 'pk')

    def test_node_set_metadata_non_string(self):
        api.node_set_metadata('free_node_0', 'JSON',
                              {"val1": 1, "val2": 2})


class TestNodeConnectDetachNetwork:

    def test_node_connect_network_success(self, switchinit):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', '3', 'node-99', '99-eth0')

        # Check the actual HTTP response and status, not just the success;
        # we should do this at least once in the test suite, since this call
        # returns 202 instead of 200 like most things.
        assert api.node_connect_network('node-99', '99-eth0', 'hammernet') == \
            ('', 202)
        deferred.apply_networking()

        network = api._must_find(model.Network, 'hammernet')
        nic = api._must_find(model.Nic, '99-eth0')
        model.NetworkAttachment.query.filter_by(network=network,
                                                nic=nic).one()

    def test_node_connect_network_wrong_node_in_project(self, switchinit):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', '3', 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')
        api.node_register('node-98', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.project_connect_node('anvil-nextgen', 'node-98')   # added

        with pytest.raises(api.NotFoundError):
            api.node_connect_network('node-98', '99-eth0', 'hammernet')

    def test_node_connect_network_wrong_node_not_in_project(self):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.node_register('node-98', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

        with pytest.raises(api.NotFoundError):
            api.node_connect_network('node-98', '99-eth0', 'hammernet')

    def test_node_connect_network_no_such_node(self):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')

        with pytest.raises(api.NotFoundError):
            api.node_connect_network('node-98', '99-eth0', 'hammernet')  # changed # noqa

    def test_node_connect_network_no_such_nic(self):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
#        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')

        with pytest.raises(api.NotFoundError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')

    def test_node_connect_network_no_such_network(self):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
#        network_create_simple('hammernet', 'anvil-nextgen')
        with pytest.raises(api.NotFoundError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')

    def test_node_connect_network_node_not_in_project(self):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
#        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')

        with pytest.raises(api.ProjectMismatchError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')

    def test_node_connect_network_different_projects(self, switchinit):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_create('anvil-oldtimer')   # added
        api.project_connect_node('anvil-nextgen', 'node-99')

        network_create_simple('hammernet', 'anvil-oldtimer')  # changed
        api.port_connect_nic('sw0', '3', 'node-99', '99-eth0')

        with pytest.raises(api.ProjectMismatchError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')

    def test_node_connect_network_already_attached_to_same(self, switchinit):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')

        api.port_connect_nic('sw0', '3', 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')  # added
        deferred.apply_networking()  # added

        with pytest.raises(api.BlockedError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')

    def test_node_connect_network_already_attached_differently(self,
                                                               switchinit):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        network_create_simple('hammernet2', 'anvil-nextgen')  # added
        api.port_connect_nic('sw0', '3', 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')  # added
        deferred.apply_networking()  # added

        with pytest.raises(api.BlockedError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet2')

    def test_node_detach_network_success(self, switchinit):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', '3', 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')
        deferred.apply_networking()  # added

        # Verify that the status is right, not just that it "succeeds."
        assert api.node_detach_network('node-99', '99-eth0', 'hammernet') \
            == ('', 202)
        deferred.apply_networking()
        network = api._must_find(model.Network, 'hammernet')
        nic = api._must_find(model.Nic, '99-eth0')
        assert model.NetworkAttachment.query \
            .filter_by(network=network, nic=nic).count() == 0

    def test_node_detach_network_not_attached(self):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
#        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(api.BadArgumentError):
            api.node_detach_network('node-99', '99-eth0', 'hammernet')

    def test_node_detach_network_wrong_node_in_project(self, switchinit):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('node-98', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_connect_node('anvil-nextgen', 'node-98')  # added
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', '3', 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.node_detach_network('node-98', '99-eth0', 'hammernet')  # changed  # noqa

    def test_node_detach_network_wrong_node_not_in_project(self, switchinit):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('node-98', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', '3', 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.node_detach_network('node-98', '99-eth0', 'hammernet')  # changed  # noqa

    def test_node_detach_network_no_such_node(self, switchinit):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', '3', 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.node_detach_network('node-98', '99-eth0', 'hammernet')  # changed  # noqa

    def test_node_detach_network_no_such_nic(self, switchinit):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', '3', 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.node_detach_network('node-99', '99-eth1', 'hammernet')  # changed  # noqa

    def test_node_detach_network_node_not_in_project(self, switchinit):
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
#        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', '3', 'node-99', '99-eth0')
#        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(api.ProjectMismatchError):
            api.node_detach_network('node-99', '99-eth0', 'hammernet')


class TestHeadnodeCreateDelete:

    def test_headnode_create_success(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        hn = api._must_find(model.Headnode, 'hn-0')
        assert hn.project.label == 'anvil-nextgen'

    def test_headnode_create_badproject(self):
        """Tests that creating a headnode with a nonexistent project fails"""
        with pytest.raises(api.NotFoundError):
            api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')

    def test_headnode_create_duplicate(self):
        """Tests that creating a headnode with a duplicate name fails"""
        api.project_create('anvil-nextgen')
        api.project_create('anvil-oldtimer')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        with pytest.raises(api.DuplicateError):
            api.headnode_create('hn-0', 'anvil-oldtimer', 'base-headnode')

    def test_headnode_create_second(self):
        """Tests that creating a second headnode one one project fails"""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create('hn-1', 'anvil-nextgen', 'base-headnode')

    def test_headnode_delete_success(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_delete('hn-0')
        api._assert_absent(model.Headnode, 'hn-0')

    def test_headnode_delete_nonexistent(self):
        """Tests that deleting a nonexistent headnode fails"""
        with pytest.raises(api.NotFoundError):
            api.headnode_delete('hn-0')


class TestHeadnodeCreateDeleteHnic:

    def test_headnode_create_hnic_success(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        nic = api._must_find(model.Hnic, 'hn-0-eth0')
        assert nic.owner.label == 'hn-0'

    def test_headnode_create_hnic_no_headnode(self):
        with pytest.raises(api.NotFoundError):
            api.headnode_create_hnic('hn-0', 'hn-0-eth0')

    def test_headnode_create_hnic_duplicate_hnic(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        with pytest.raises(api.DuplicateError):
            api.headnode_create_hnic('hn-0', 'hn-0-eth0')

    def test_headnode_delete_hnic_success(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        api.headnode_delete_hnic('hn-0', 'hn-0-eth0')
        api._assert_absent(model.Hnic, 'hn-0-eth0')
        hn = api._must_find(model.Headnode, 'hn-0')

    def test_headnode_delete_hnic_hnic_nexist(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        with pytest.raises(api.NotFoundError):
            api.headnode_delete_hnic('hn-0', 'hn-0-eth0')

    def test_headnode_delete_hnic_headnode_nexist(self):
        with pytest.raises(api.NotFoundError):
            api.headnode_delete_hnic('hn-0', 'hn-0-eth0')

    def test_headnode_delete_hnic_wrong_headnode(self):
        api.project_create('anvil-nextgen')
        api.project_create('anvil-oldtimer')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create('hn-1', 'anvil-oldtimer', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        with pytest.raises(api.NotFoundError):
            api.headnode_delete_hnic('hn-1', 'hn-0-eth0')

    def test_headnode_delete_hnic_wrong_nexist_headnode(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        with pytest.raises(api.NotFoundError):
            api.headnode_delete_hnic('hn-1', 'hn-0-eth0')

    def test_headnode_create_hnic_diff_headnodes(self):
        api.project_create('anvil-legacy')
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-legacy', 'base-headnode')
        api.headnode_create('hn-1', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'eth0')
        api.headnode_create_hnic('hn-1', 'eth0')


class TestHeadnodeConnectDetachNetwork:

    def test_headnode_connect_network_success(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')

        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')
        network = api._must_find(model.Network, 'hammernet')
        hnic = api._must_find(model.Hnic, 'hn-0-eth0')
        assert hnic.network is network
        assert hnic in network.hnics

    def test_headnode_connect_network_no_such_headnode(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')

        with pytest.raises(api.NotFoundError):
            api.headnode_connect_network('hn-1', 'hn-0-eth0', 'hammernet')  # changed  # noqa

    def test_headnode_connect_network_no_such_hnic(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')

        with pytest.raises(api.NotFoundError):
            api.headnode_connect_network('hn-0', 'hn-0-eth1', 'hammernet')  # changed  # noqa

    def test_headnode_connect_network_no_such_network(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')

        with pytest.raises(api.NotFoundError):
            api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet2')  # changed  # noqa

    def test_headnode_connect_network_already_attached_to_same(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')  # added

        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

    def test_headnode_connect_network_already_attached_differently(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')
        network_create_simple('hammernet2', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')  # added

        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet2')  # changed  # noqa

    def test_headnode_connect_network_different_projects(self):
        api.project_create('anvil-nextgen')
        api.project_create('anvil-oldtimer')  # added
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-oldtimer')  # changed

        with pytest.raises(api.ProjectMismatchError):
            api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

    def test_headnode_connect_network_non_allocated(self):
        """Connecting a headnode to a non-allocated network should fail.

        Right now the create_bridges script will only create bridges
        for vlans in the database, so any specified by the administrator
        will not exist. Since the haas does not create the bridges during
        execution, attempting to attach a headnode to a network whose vlan
        does not have an existing bridge will fail. An administrator could
        work around this by creating the bridges manually, but we wish to
        treat the naming of the bridges as an implementation detail as much
        as possible, and thus discourage this.

        For now connecting headnodes to non-allocated networks is simply
        not supported; this will change in the future. In the meantime,
        we should report a sensible error, and this test checks for that.

        See also issue #333
        """
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        api.network_create('hammernet', 'admin', 'anvil-nextgen', '7')
        with pytest.raises(api.BadArgumentError):
            api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

    def test_headnode_detach_network_success(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

        api.headnode_detach_network('hn-0', 'hn-0-eth0')
        network = api._must_find(model.Network, 'hammernet')
        hnic = api._must_find(model.Hnic, 'hn-0-eth0')
        assert hnic.network is None
        assert hnic not in network.hnics

    def test_headnode_detach_network_not_attached(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')
#        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

        api.headnode_detach_network('hn-0', 'hn-0-eth0')

    def test_headnode_detach_network_no_such_headnode(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.headnode_detach_network('hn-1', 'hn-0-eth0')  # changed

    def test_headnode_detach_network_no_such_hnic(self):
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.headnode_detach_network('hn-0', 'hn-0-eth1')  # changed


class TestHeadnodeFreeze:

    # We can't start the headnodes for real in the test suite, but we need
    # "starting" them to still clear the dirty bit.
    @pytest.fixture(autouse=True)
    def patch_start(self, monkeypatch):
        def start(self):
            self.dirty = False
        monkeypatch.setattr(model.Headnode, 'start', start)

    def _prep(self):
        """Helper to set up common state."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')

    def _prep_delete_hnic(self):
        self._prep()
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')

    def _prep_connect_network(self):
        """Helper to set up common state for headnode_connect_network tests."""
        self._prep()
        network_create_simple('hammernet', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')

    def _prep_detach_network(self):
        self._prep_connect_network()
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

    def test_freeze_fail_create_hnic(self):
        self._prep()

        api.headnode_start('hn-0')
        with pytest.raises(api.IllegalStateError):
            api.headnode_create_hnic('hn-0', 'hn-0-eth0')

    def test_succeed_create_hnic(self):
        self._prep()

        api.headnode_create_hnic('hn-0', 'hn-0-eth0')

    def test_freeze_fail_delete_hnic(self):
        self._prep_delete_hnic()

        api.headnode_start('hn-0')
        with pytest.raises(api.IllegalStateError):
            api.headnode_delete_hnic('hn-0', 'hn-0-eth0')

    def test_succeed_delete_hnic(self):
        self._prep_delete_hnic()

        api.headnode_delete_hnic('hn-0', 'hn-0-eth0')

    def test_freeze_fail_connect_network(self):
        self._prep_connect_network()

        api.headnode_start('hn-0')
        with pytest.raises(api.IllegalStateError):
            api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

    def test_succeed_connect_network(self):
        self._prep_connect_network()

        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

    def test_freeze_fail_detach_network(self):
        self._prep_detach_network()

        api.headnode_start('hn-0')
        with pytest.raises(api.IllegalStateError):
            api.headnode_detach_network('hn-0', 'hn-0-eth0')

    def test_succeed_detach_network(self):
        self._prep_detach_network()

        api.headnode_detach_network('hn-0', 'hn-0-eth0')


class TestNetworkCreateDelete:
    """Tests for the haas.api.network_* functions."""

    def test_network_create_success(self):
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        net = api._must_find(model.Network, 'hammernet')
        assert net.owner.label == 'anvil-nextgen'

    def test_network_create_badproject(self):
        """Tests that creating a network with a nonexistent project fails"""
        with pytest.raises(api.NotFoundError):
            network_create_simple('hammernet', 'anvil-nextgen')

    def test_network_create_duplicate(self):
        """Tests that creating a network with a duplicate name fails"""
        api.project_create('anvil-nextgen')
        api.project_create('anvil-oldtimer')
        network_create_simple('hammernet', 'anvil-nextgen')
        with pytest.raises(api.DuplicateError):
            network_create_simple('hammernet', 'anvil-oldtimer')

    def test_network_delete_success(self):
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.network_delete('hammernet')
        api._assert_absent(model.Network, 'hammernet')

    def test_network_delete_project_complex_success(self, switchinit):
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:14')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.port_connect_nic('sw0', '3', 'node-99', 'eth0')
        api.node_connect_network('node-99', 'eth0', 'hammernet')
        deferred.apply_networking()
        api.node_detach_network('node-99', 'eth0', 'hammernet')
        deferred.apply_networking()
        api.network_delete('hammernet')

    def test_network_delete_nonexistent(self):
        """Tests that deleting a nonexistent network fails"""
        with pytest.raises(api.NotFoundError):
            api.network_delete('hammernet')

    def test_network_delete_node_on_network(self, switchinit):
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:14')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.port_connect_nic('sw0', '3', 'node-99', 'eth0')
        api.node_connect_network('node-99', 'eth0', 'hammernet')
        with pytest.raises(api.BlockedError):
            api.network_delete('hammernet')

    def test_network_delete_headnode_on_network(self):
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'eth0')
        api.headnode_connect_network('hn-0', 'eth0', 'hammernet')
        with pytest.raises(api.BlockedError):
            api.network_delete('hammernet')


class TestSwitch:

    def test_register(self):
        """Calling switch_register should create an object in the db."""
        api.switch_register('sw0', type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        assert model.Switch.query.one().label == 'sw0'

    def test_register_duplicate(self):
        """switch_register should complain if asked to make a duplicate switch.
        """
        api.switch_register('sw0', type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        with pytest.raises(api.DuplicateError):
            api.switch_register('sw0', type=MOCK_SWITCH_TYPE,
                                username="switch_user",
                                password="switch_pass",
                                hostname="switchname")


class Test_switch_delete:

    def test_delete(self):
        """Deleting a switch should actually remove it."""
        api.switch_register('sw0', type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_delete('sw0')
        assert model.Switch.query.count() == 0

    def test_delete_nonexisting(self):
        """
        switch_delete should complain if asked to delete a switch
        that doesn't exist.
        """
        with pytest.raises(api.NotFoundError):
            api.switch_delete('sw0')


class Test_switch_register_port:

    def test_register_port(self):
        """Creating a port on an existing switch should succeed."""
        api.switch_register('sw0', type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_register_port('sw0', '5')
        port = model.Port.query.one()
        assert port.label == '5'
        assert port.owner.label == 'sw0'

    def test_register_port_nonexisting_switch(self):
        """Creating  port on a non-existant switch should fail."""
        with pytest.raises(api.NotFoundError):
            api.switch_register_port('sw0', '5')


class Test_switch_delete_port:

    def test_delete_port(self):
        """Removing a port should remove it from the db."""
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_register_port('sw0', '5')
        api.switch_delete_port('sw0', '5')
        assert model.Port.query.count() == 0

    def test_delete_port_nonexisting_switch(self):
        """
        Removing a port on a switch that does not exist should
        report the error.
        """
        with pytest.raises(api.NotFoundError):
            api.switch_delete_port('sw0', '5')

    def test_delete_port_nonexisting_port(self):
        """Removing a port that does not exist should report the error"""
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        with pytest.raises(api.NotFoundError):
            api.switch_delete_port('sw0', '5')


class Test_list_switches:

    def test_list_switches(self):
        assert json.loads(api.list_switches()) == []

        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="foo",
                            password="bar",
                            hostname="baz")
        api._must_find(model.Switch, 'sw0')
        assert json.loads(api.list_switches()) == ['sw0']

        api.switch_register('mock',
                            type=MOCK_SWITCH_TYPE,
                            username="user",
                            password="password",
                            hostname="host")
        api._must_find(model.Switch, 'mock')

        api.switch_register('cirius',
                            type=MOCK_SWITCH_TYPE,
                            username="user",
                            password="password",
                            hostname="switch")

        api._must_find(model.Switch, 'cirius')
        assert json.loads(api.list_switches()) == [
            'cirius',
            'mock',
            'sw0',
        ]

    def test_show_switch(self, switchinit):

        assert json.loads(api.show_switch('sw0')) == {
            'name': 'sw0',
            'ports': [{'label': '3'}]
        }

        api.switch_register_port('sw0', 'test_port')
        # Note: the order of ports is not sorted, test cases need to be in the
        # same order.
        assert json.loads(api.show_switch('sw0')) == {
            'name': 'sw0',
            'ports': [{'label': '3'},
                      {'label': 'test_port'}]
        }


class TestPortConnectDetachNic:

    def test_port_connect_nic_success(self, switchinit):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('sw0', '3', 'compute-01', 'eth0')

    def test_port_connect_nic_no_such_switch(self):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.port_connect_nic('sw0', '3', 'compute-01', 'eth0')

    def test_port_connect_nic_no_such_port(self):
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.port_connect_nic('sw0', '3', 'compute-01', 'eth0')

    def test_port_connect_nic_no_such_node(self):
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_register_port('sw0', '3')
        with pytest.raises(api.NotFoundError):
            api.port_connect_nic('sw0', '3', 'compute-01', 'eth0')

    def test_port_connect_nic_no_such_nic(self):
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_register_port('sw0', '3')
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        with pytest.raises(api.NotFoundError):
            api.port_connect_nic('sw0', '3', 'compute-01', 'eth0')

    def test_port_connect_nic_already_attached_to_same(self, switchinit):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('sw0', '3', 'compute-01', 'eth0')
        with pytest.raises(api.DuplicateError):
            api.port_connect_nic('sw0', '3', 'compute-01', 'eth0')

    def test_port_connect_nic_nic_already_attached_differently(self,
                                                               switchinit):
        api.switch_register_port('sw0', '4')
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('sw0', '3', 'compute-01', 'eth0')
        with pytest.raises(api.DuplicateError):
            api.port_connect_nic('sw0', '4', 'compute-01', 'eth0')

    def test_port_connect_nic_port_already_attached_differently(self,
                                                                switchinit):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register('compute-02', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.node_register_nic('compute-02', 'eth1', 'DE:AD:BE:EF:20:15')
        api.port_connect_nic('sw0', '3', 'compute-01', 'eth0')
        with pytest.raises(api.DuplicateError):
            api.port_connect_nic('sw0', '3', 'compute-02', 'eth1')

    def test_port_detach_nic_success(self, switchinit):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('sw0', '3', 'compute-01', 'eth0')
        api.port_detach_nic('sw0', '3')

    def test_port_detach_nic_no_such_port(self):
        with pytest.raises(api.NotFoundError):
            api.port_detach_nic('sw0', '3')

    def test_port_detach_nic_not_attached(self):
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_register_port('sw0', '3')
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.port_detach_nic('sw0', '3')

    def port_detach_nic_node_not_free(self, switchinit):
        """should refuse to detach a nic if it has pending actions."""
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('sw0', '3', 'compute-01', 'eth0')

        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'compute-01')

        with pytest.raises(api.BlockedError):
            api.port_detach_nic('sw0', '3')


class TestQuery_populated_db:
    """test portions of the query api with a populated database"""

    pytestmark = pytest.mark.usefixtures(*(default_fixtures +
                                           ['additional_database']))

    def test_list_networks(self):
        result = json.loads(api.list_networks())
        for net in result.keys():
            del result[net]['network_id']
        assert result == {
            'manhattan_provider': {'projects': ['manhattan']},
            'manhattan_pxe': {'projects': ['manhattan']},
            'manhattan_runway_provider': {'projects': ['manhattan', 'runway']},
            'manhattan_runway_pxe': {'projects': ['manhattan', 'runway']},
            'pub_default': {'projects': None},
            'runway_provider': {'projects': ['runway']},
            'runway_pxe': {'projects': ['runway']},
            'stock_ext_pub': {'projects': None},
            'stock_int_pub': {'projects': None},
        }

    def test_list_network_attachments(self):
        api.node_connect_network(
            'runway_node_0', 'boot-nic', 'manhattan_runway_pxe')
        api.node_connect_network(
            'manhattan_node_0', 'boot-nic', 'manhattan_runway_pxe')
        deferred.apply_networking()

        actual = json.loads(
            api.list_network_attachments('manhattan_runway_pxe'))
        expected = {
            'manhattan_node_0':
                {
                    'nic': 'boot-nic',
                    'channel': get_network_allocator().get_default_channel(),
                    'project': 'manhattan'
                },
            'runway_node_0':
                {
                    'nic': 'boot-nic',
                    'channel': get_network_allocator().get_default_channel(),
                    'project': 'runway'
                }
            }
        assert actual == expected

    def test_list_network_attachments_for_project(self):
        api.node_connect_network(
            'runway_node_0',
            'boot-nic',
            'manhattan_runway_pxe')
        api.node_connect_network(
            'manhattan_node_0',
            'boot-nic',
            'manhattan_runway_pxe')
        deferred.apply_networking()

        actual = json.loads(
            api.list_network_attachments('manhattan_runway_pxe', 'runway'))
        expected = {
            'runway_node_0':
                {
                    'nic': 'boot-nic',
                    'channel': get_network_allocator().get_default_channel(),
                    'project': 'runway'
                }
            }
        assert actual == expected


class TestQuery_unpopulated_db:
    """test portions of the query api with a fresh database"""

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
        for key, value in actual['metadata'].iteritems():
            assert key in expected['metadata']
            assert expected['metadata'][key] == value
            del expected['metadata'][key]
        assert len(expected['metadata']) == 0
        actual['metadata'] = {}
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
        result = json.loads(api.list_nodes("free"))
        # For the lists to be equal, the ordering must be the same:
        result.sort()
        assert result == [
            'data',
            'master-control-program',
            'robocop',
        ]

    def test_list_networks_none(self):
        assert json.loads(api.list_networks()) == {}

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
        assert json.loads(api.list_nodes("ree")) == []

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

        assert json.loads(api.list_nodes("free")) == ['master-control-program']

    def test_show_node(self):
        """Test the show_node api call.

        We create a node, and query it twice: once before it is reserved,
        and once after it has been reserved by a project and attached to
        a network. Two things should change: (1) "project" should show
        registered project, and (2) the newly attached network should be
        listed.
        """
        api.node_register('robocop', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('robocop', 'eth0', 'DE:AD:BE:EF:20:14')
        api.node_register_nic('robocop', 'wlan0', 'DE:AD:BE:EF:20:15')
        api.node_set_metadata('robocop', 'EK', 'pk')
        api.node_set_metadata('robocop', 'SHA256', 'b5962d8173c14e6025921'
                              '1bcf25d1263c36e0ad7da32ba9d07b224eac18'
                              '34813')

        actual = json.loads(api.show_node('robocop'))
        expected = {
            'name': 'robocop',
            'project': None,
            'nics': [
                {
                    'label': 'eth0',
                    'macaddr': 'DE:AD:BE:EF:20:14',
                    "networks": {}
                },
                {
                    'label': 'wlan0',
                    'macaddr': 'DE:AD:BE:EF:20:15',
                    "networks": {}
                }
            ],
            'metadata': {
                'EK': json.dumps('pk'),
                'SHA256': json.dumps('b5962d8173c14e60259211bcf25d1263c36e0'
                                     'ad7da32ba9d07b224eac1834813')
            }
        }
        self._compare_node_dumps(actual, expected)

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
                    'label': 'eth0',
                    'macaddr': 'DE:AD:BE:EF:20:14',
                    "networks": {}
                },
                {
                    'label': 'wlan0',
                    'macaddr': 'DE:AD:BE:EF:20:15',
                    "networks": {}
                }
            ],
            'metadata': {}
        }
        self._compare_node_dumps(actual, expected)

    def test_show_node_multiple_network(self):
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_register_port('sw0', '1')
        api.switch_register_port('sw0', '2')
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
        api.port_connect_nic('sw0', '1', 'robocop', 'eth0')
        api.node_connect_network('robocop', 'eth0', 'pxe')
        network_create_simple('storage', 'anvil-nextgen')
        api.port_connect_nic('sw0', '2', 'robocop', 'wlan0')
        api.node_connect_network('robocop', 'wlan0', 'storage')
        deferred.apply_networking()

        actual = json.loads(api.show_node('robocop'))
        expected = {
            'name': 'robocop',
            'project': 'anvil-nextgen',
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
                        get_network_allocator().get_default_channel(): 'storage'  # noqa
                    }
                }
            ],
            'metadata': {}
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
        assert result == ['base-headnode', 'img1', 'img2', 'img3', 'img4']


class TestShowNetwork:
    """Test the show_network api cal."""

    def test_show_network_simple(self):
        api.project_create('anvil-nextgen')
        network_create_simple('spiderwebs', 'anvil-nextgen')

        result = json.loads(api.show_network('spiderwebs'))
        assert result == {
            'name': 'spiderwebs',
            'owner': 'anvil-nextgen',
            'access': ['anvil-nextgen'],
            "channels": ["null"]
        }

    def test_show_network_public(self):
        api.network_create('public-network',
                           owner='admin',
                           access='',
                           net_id='432')

        result = json.loads(api.show_network('public-network'))
        assert result == {
            'name': 'public-network',
            'owner': 'admin',
            'access': None,
            'channels': ['null'],
        }

    def test_show_network_provider(self):
        api.project_create('anvil-nextgen')
        api.network_create('spiderwebs',
                           owner='admin',
                           access='anvil-nextgen',
                           net_id='451')

        result = json.loads(api.show_network('spiderwebs'))
        assert result == {
            'name': 'spiderwebs',
            'owner': 'admin',
            'access': ['anvil-nextgen'],
            'channels': ['null'],
        }


class TestFancyNetworkCreate:
    """Test creating network with advanced parameters.

    These test the 10 possible combinations of creator project, access
    project, and underlying net-id.  It confirms that the legal ones are
    allowed, and that their parameters are passed into the database
    succesfully, and confirms the the prohibited ones are disallowed.

    The details of these combinations are shown in docs/networks.md
    """

    def test_project_network(self):
        """Succesfully create a project-owned network."""
        api.project_create('anvil-nextgen')
        api.network_create('hammernet', 'anvil-nextgen', 'anvil-nextgen', '')
        project = api._must_find(model.Project, 'anvil-nextgen')
        network = api._must_find(model.Network, 'hammernet')
        assert network.owner is project
        assert project in network.access
        assert network.allocated is True

    def test_project_network_imported_fails(self):
        """Fail to make a project-owned network with a supplied net-id."""
        api.project_create('anvil-nextgen')
        with pytest.raises(api.BadArgumentError):
            api.network_create('hammernet',
                               'anvil-nextgen',
                               'anvil-nextgen',
                               '35')

    def test_project_network_bad_access_fails(self):
        """Fail to make a project-owned network that others can access."""
        api.project_create('anvil-nextgen')
        api.project_create('anvil-oldtimer')
        for access in ['', 'anvil-oldtimer']:
            for net_id in ['', '35']:
                with pytest.raises(api.BadArgumentError):
                    api.network_create('hammernet',
                                       'anvil-nextgen',
                                       access, net_id)

    def test_admin_network(self):
        """
        Succesfully create all 4 varieties of administrator-owned networks.
        """
        api.project_create('anvil-nextgen')
        project = api._must_find(model.Project, 'anvil-nextgen')
        for project_api, project_db in [('', None),
                                        ('anvil-nextgen', project)]:
            for net_id, allocated in [('', True), ('35', False)]:
                network = 'hammernet' + project_api + net_id
                api.network_create(network, 'admin', project_api, net_id)
                network = api._must_find(model.Network, network)
                assert network.owner is None
                if project_db is None:
                    assert not network.access
                else:
                    assert project_db in network.access
                assert network.allocated is allocated
            network = api._must_find(model.Network, 'hammernet' +
                                     project_api + '35')
            assert network.network_id == '35'


class TestDryRun:
    """
    Test that api calls using functions with @no_dry_run behave reasonably.
    """

    def test_node_power_cycle(self):
        """Check that power-cycle behaves reasonably under @no_dry_run."""
        api.project_create('anvil-nextgen')
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.node_power_cycle('node-99')
