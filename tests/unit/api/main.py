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

"""Unit tests for hil.api

Some general notes:

Probably most of our technical debt is in this module; about 75% of it
was written in one day by one person, way back when the HIL codebase
was somewhat embarassing, we basically didn't have a test suite, and
we decided we needed one in a hurry. The biggest problem is that it's
a bit difficult to tell what properties a test is verifying, since
there's lots of setup code mixed in with the actual check. Unfortunately,
the setup code isn't really regular enough to factor out into one fixture.

A few efforts have been made to make reading the tests a bit easier to
navigate:

* In some places, you'll see a statement making some api call commented
  out. This is a hint that this test is similar to another one near by,
  which has that statement un-commented.
* Some lines have a comment "# changed" after them. This indicates that
  nearby tests have a similar line, but something has been changed from
  those lines (perhaps a single argument has a different value for
  example).
* When two tests are very similar in what they test, the docstrings say
  things like "same as above, but with foo instead of bar." Make sure when
  modifying this file you don't change things such that those references are
  no longer correct.

General advice on working with this module:

* Leave the code in better condition than you found it.
* Be wary of comments that make broad statements about what operations are
  supported, particulary if that test doesn't actually verify that property;
  sometimes the way HIL works changes, and we have historically not been
  very good at updating every comment in here to match.
* Accordingly, avoid writing comments that state things about HIL that the
  test doesn't verify; this file is huge and you're never going to remember
  to update those statements if the changes don't cause failures.
* With new tests, cleanly separate setup code from the actual tests. This
  might take the form of a single setUp() method on a class that holds
  similar tests, or the use of a fixture. Just make sure it improves
  readability and maintainability.
* make sure it is easy to see what a new test is trying to verify.
"""
import hil
from hil import model, deferred, errors, config, api
from hil.test_common import config_testsuite, config_merge, fresh_database, \
    fail_on_log_warnings, additional_db, with_request_context, \
    network_create_simple, server_init
from hil.network_allocator import get_network_allocator
from hil.auth import get_auth_backend
import pytest
import json
import uuid

MOCK_SWITCH_TYPE = 'http://schema.massopencloud.org/haas/v0/switches/mock'
OBM_TYPE_MOCK = 'http://schema.massopencloud.org/haas/v0/obm/mock'
OBM_TYPE_IPMI = 'http://schema.massopencloud.org/haas/v0/obm/ipmi'
PORTS = ['gi1/0/1', 'gi1/0/2', 'gi1/0/3', 'gi1/0/4', 'gi1/0/5']


@pytest.fixture
def configure():
    """Configure HIL"""
    config_testsuite()
    config_merge({
        'auth': {
            'require_authentication': 'True',
        },
        'extensions': {
            'hil.ext.auth.null': None,
            'hil.ext.auth.mock': '',
            'hil.ext.switches.mock': '',
            'hil.ext.obm.ipmi': '',
            'hil.ext.obm.mock': '',
            'hil.ext.network_allocators.null': None,
            'hil.ext.network_allocators.vlan_pool': '',
        },
        'hil.ext.network_allocators.vlan_pool': {
            'vlans': '40-80',
        },
    })
    config.load_extensions()


fresh_database = pytest.fixture(fresh_database)
additional_database = pytest.fixture(additional_db)
fail_on_log_warnings = pytest.fixture(fail_on_log_warnings)
server_init = pytest.fixture(server_init)


with_request_context = pytest.yield_fixture(with_request_context)


@pytest.fixture
def set_admin_auth():
    """Set admin auth for all calls"""
    get_auth_backend().set_admin(True)


@pytest.fixture
def switchinit():
    """Create a switch with one port"""
    api.switch_register('sw0',
                        type=MOCK_SWITCH_TYPE,
                        username="switch_user",
                        password="switch_pass",
                        hostname="switchname")
    api.switch_register_port('sw0', PORTS[2])


def new_node(name):
    """Create a mock node named ``name``"""
    api.node_register(name, obm={
              "type": OBM_TYPE_MOCK,
              "host": "ipmihost",
              "user": "root",
              "password": "tapeworm"})


default_fixtures = ['fail_on_log_warnings',
                    'configure',
                    'fresh_database',
                    'server_init',
                    'with_request_context',
                    'set_admin_auth']

pytestmark = pytest.mark.usefixtures(*default_fixtures)


class TestProjectCreateDelete:
    """Tests for the hil.api.project_{create,delete} functions."""

    pytestmark = pytest.mark.usefixtures(*(default_fixtures +
                                           ['additional_database']))

    def test_project_create_success(self):
        """(successful) call to project_create"""
        api.project_create('anvil-nextgen')
        api._must_find(model.Project, 'anvil-nextgen')

    def test_project_create_duplicate(self):
        """Call to project_create should fail if the project already exists."""
        with pytest.raises(errors.DuplicateError):
            api.project_create('manhattan')

    def test_project_delete(self):
        """project_delete should successfully delete a project."""
        api.project_delete('empty-project')
        with pytest.raises(errors.NotFoundError):
            api._must_find(model.Project, 'empty-project')

    def test_project_delete_nexist(self):
        """Deleting a project which doesn't exist should raise not found."""
        with pytest.raises(errors.NotFoundError):
            api.project_delete('anvil-nextgen')

    def test_project_delete_hasnode(self):
        """Deleting a project which has nodes should fail."""
        with pytest.raises(errors.BlockedError):
            api.project_delete('manhattan')

    def test_project_delete_success_nodesdeleted(self):
        """...but after deleting the nodes, should succeed."""
        new_node('node-99')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_detach_node('anvil-nextgen', 'node-99')
        api.project_delete('anvil-nextgen')

    def test_project_delete_hasnetwork(self):
        """Deleting a project that has networks should fail."""
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        with pytest.raises(errors.BlockedError):
            api.project_delete('anvil-nextgen')

    def test_project_delete_success_networksdeleted(self):
        """...but after deleting the networks, should succeed."""
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.network_delete('hammernet')
        api.project_delete('anvil-nextgen')

    def test_project_delete_hasheadnode(self):
        """Deleting a project that has headnodes should fail."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-01', 'anvil-nextgen', 'base-headnode')
        with pytest.raises(errors.BlockedError):
            api.project_delete('anvil-nextgen')

    def test_duplicate_project_create(self):
        """Creating a project that already exists should fail."""
        api.project_create('acme-corp')
        with pytest.raises(errors.DuplicateError):
            api.project_create('acme-corp')


class TestProjectAddDeleteNetwork:
    """Tests for adding and deleting a network from a project"""

    pytestmark = pytest.mark.usefixtures(*(default_fixtures +
                                           ['additional_database']))

    def test_network_grant_project_access(self):
        """network_grant_project_access should actually grant access."""
        api.network_grant_project_access('manhattan', 'runway_pxe')
        network = api._must_find(model.Network, 'runway_pxe')
        project = api._must_find(model.Project, 'manhattan')
        assert project in network.access
        assert network in project.networks_access

    def test_network_revoke_project_access(self):
        """network_revoke_project_access should actually revoke access."""
        api.network_revoke_project_access('runway', 'runway_provider')
        network = api._must_find(model.Network, 'runway_provider')
        project = api._must_find(model.Project, 'runway')
        assert project not in network.access
        assert network not in project.networks_access

    def test_network_revoke_project_access_connected_node(self):
        """Test reovking access to a project that has nodes on the network.

        This should fail.
        """
        api.node_connect_network(
            'runway_node_0',
            'boot-nic',
            'runway_provider')
        deferred.apply_networking()

        with pytest.raises(errors.BlockedError):
            api.network_revoke_project_access('runway', 'runway_provider')

    def test_project_remove_network_owner(self):
        """Revoking access to a network's owner should fail."""
        with pytest.raises(errors.BlockedError):
            api.network_revoke_project_access('runway', 'runway_pxe')


class TestNetworking:
    """Misc. Networking related tests."""

    def test_networking_involved(self):
        """Do a bunch of network related operations."""
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        for port in PORTS[0], PORTS[1], PORTS[2]:
            api.switch_register_port('sw0', port)
        new_node('node-99')
        new_node('node-98')
        new_node('node-97')

        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:14')
        api.node_register_nic('node-98', 'eth0', 'DE:AD:BE:EF:20:15')
        api.node_register_nic('node-97', 'eth0', 'DE:AD:BE:EF:20:16')
        for port, node in (PORTS[0], 'node-99'), (PORTS[1], 'node-98'), \
                          (PORTS[2], 'node-97'):
            api.port_connect_nic('sw0', port, node, 'eth0')

        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_connect_node('anvil-nextgen', 'node-98')
        network_create_simple('hammernet', 'anvil-nextgen')
        network_create_simple('spiderwebs', 'anvil-nextgen')
        api.node_connect_network('node-98', 'eth0', 'hammernet')

    def test_networking_nic_no_port(self):
        """Connecting a nic with no port to a network should fail."""
        new_node('node-99')
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:14')

        api.project_create('anvil-nextgen')

        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        with pytest.raises(errors.NotFoundError):
            api.node_connect_network('node-99', 'eth0', 'hammernet')


class TestProjectConnectDetachNode:
    """Test project_{connect,detach}_node."""

    def test_project_connect_node(self):
        """Check that project_connect_node adds the node to the project."""
        api.project_create('anvil-nextgen')
        new_node('node-99')

        api.project_connect_node('anvil-nextgen', 'node-99')
        project = api._must_find(model.Project, 'anvil-nextgen')
        node = api._must_find(model.Node, 'node-99')
        assert node in project.nodes
        assert node.project is project

    def test_project_connect_node_project_nexist(self):
        """Tests that connecting a node to a nonexistent project fails"""
        new_node('node-99')
        with pytest.raises(errors.NotFoundError):
            api.project_connect_node('anvil-nextgen', 'node-99')

    def test_project_connect_node_node_nexist(self):
        """Tests that connecting a nonexistent node to a projcet fails"""
        api.project_create('anvil-nextgen')
        with pytest.raises(errors.NotFoundError):
            api.project_connect_node('anvil-nextgen', 'node-99')

    def test_project_connect_node_node_busy(self):
        """Connecting a node which is not free to a project should fail."""
        new_node('node-99')

        api.project_create('anvil-oldtimer')
        api.project_create('anvil-nextgen')

        api.project_connect_node('anvil-oldtimer', 'node-99')
        with pytest.raises(errors.BlockedError):
            api.project_connect_node('anvil-nextgen', 'node-99')

    def test_project_detach_node(self):
        """Test that project_detach_node removes the node from the project."""
        api.project_create('anvil-nextgen')
        new_node('node-99')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_detach_node('anvil-nextgen', 'node-99')
        project = api._must_find(model.Project, 'anvil-nextgen')
        node = api._must_find(model.Node, 'node-99')
        assert node not in project.nodes
        assert node.project is not project

    def test_project_detach_node_notattached(self):
        """Tests that removing a node from a project it's not in fails."""
        api.project_create('anvil-nextgen')
        new_node('node-99')
        with pytest.raises(errors.NotFoundError):
            api.project_detach_node('anvil-nextgen', 'node-99')

    def test_project_detach_node_project_nexist(self):
        """Tests that removing a node from a nonexistent project fails."""
        new_node('node-99')
        with pytest.raises(errors.NotFoundError):
            api.project_detach_node('anvil-nextgen', 'node-99')

    def test_project_detach_node_node_nexist(self):
        """Tests that removing a nonexistent node from a project fails."""
        api.project_create('anvil-nextgen')
        with pytest.raises(errors.NotFoundError):
            api.project_detach_node('anvil-nextgen', 'node-99')

    def test_project_detach_node_on_network(self, switchinit):
        """Tests that project_detach_node fails if the node is on a network."""
        api.project_create('anvil-nextgen')
        new_node('node-99')
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:13')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', PORTS[2], 'node-99', 'eth0')
        api.node_connect_network('node-99', 'eth0', 'hammernet')
        with pytest.raises(errors.BlockedError):
            api.project_detach_node('anvil-nextgen', 'node-99')

    def test_project_detach_node_success_nic_not_on_network(self):
        """...but succeeds if not, all else being equal."""
        api.project_create('anvil-nextgen')
        new_node('node-99')
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:13')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.project_detach_node('anvil-nextgen', 'node-99')

    def test_project_detach_node_removed_from_network(self, switchinit):
        """Same as above, but we connect/disconnect from the network.

        ...rather than just having the node disconnected to begin with.
        """
        api.project_create('anvil-nextgen')
        new_node('node-99')
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:13')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', PORTS[2], 'node-99', 'eth0')
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
        """...for the ipmi driver."""
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

        node_obj = model.Node.query.filter_by(label="compute-01")\
                        .join(model.Obm).join(hil.ext.obm.ipmi.Ipmi).one()

        # Comes from table node
        assert str(node_obj.label) == 'compute-01'
        # Comes from table obm
        assert str(node_obj.obm.api_name) == OBM_TYPE_IPMI
        # Comes from table ipmi
        assert str(node_obj.obm.host) == 'ipmihost'

    def test_mockobm(self):
        """...for the mock driver."""
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/mock",
                  "host": "mockObmhost",
                  "user": "root",
                  "password": "tapeworm"})

        node_obj = model.Node.query.filter_by(label="compute-01")\
                        .join(model.Obm).join(hil.ext.obm.mock.MockObm).one()  # noqa

        # Comes from table node
        assert str(node_obj.label) == 'compute-01'
        # Comes from table obm
        assert str(node_obj.obm.api_name) == OBM_TYPE_MOCK
        # Comes from table mockobm
        assert str(node_obj.obm.host) == 'mockObmhost'


class TestNodeRegisterDelete:
    """Tests for the hil.api.node_{register,delete} functions."""

    def test_node_register(self):
        """node_register should add the node to the db."""
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api._must_find(model.Node, 'node-99')

    def test_node_register_with_metadata(self):
        """Same thing, but try it with metadata."""
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
        """...and with the metadata being something other than a string."""
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
        """...and with multiple metadata keys."""
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
        """Duplicate calls to node_register should fail."""
        new_node('node-99')
        with pytest.raises(errors.DuplicateError):
            new_node('node-99')

    def test_node_delete(self):
        """node_delete should remove the node from the db."""
        new_node('node-99')
        api.node_delete('node-99')
        with pytest.raises(errors.NotFoundError):
            api._must_find(model.Node, 'node-99')

    def test_node_delete_nexist(self):
        """node_delete should fail if the node does not exist."""
        with pytest.raises(errors.NotFoundError):
            api.node_delete('node-99')

    def test_node_delete_nic_exist(self):
        """node_delete should respond with an error if the node has nics."""
        new_node('node-99')
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(errors.BlockedError):
            api.node_delete('node-99')

    def test_node_delete_in_project(self):
        """node_delete should respond with an error if node is in project"""
        new_node('node-99')
        api.project_create('skeleton')
        api.project_connect_node('skeleton', 'node-99')
        with pytest.raises(errors.BlockedError):
            api.node_delete('node-99')


class TestNodeRegisterDeleteNic:
    """Test node_{register,delete}_nic."""

    def test_node_register_nic(self):
        """node_register_nic should add the nic to the db."""
        new_node('compute-01')
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        nic = api._must_find(model.Nic, '01-eth0')
        assert nic.owner.label == 'compute-01'

    def test_node_register_nic_no_node(self):
        """node_register_nic should fail if the node does not exist."""
        with pytest.raises(errors.NotFoundError):
            api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')

    def test_node_register_nic_duplicate_nic(self):
        """node_register_nic should fail if the nic already exists."""
        new_node('compute-01')
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        api._must_find(model.Nic, '01-eth0')
        with pytest.raises(errors.DuplicateError):
            api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:15')

    def test_node_delete_nic_success(self):
        """node_delete_nic should remove the nic from the db.

        However, it should *not* remove the node.
        """
        new_node('compute-01')
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        api.node_delete_nic('compute-01', '01-eth0')
        api._assert_absent(model.Nic, '01-eth0')
        api._must_find(model.Node, 'compute-01')

    def test_node_delete_nic_nic_nexist(self):
        """node_delete_nic should fail if the nic does not exist."""
        new_node('compute-01')
        with pytest.raises(errors.NotFoundError):
            api.node_delete_nic('compute-01', '01-eth0')

    def test_node_delete_nic_node_nexist(self):
        """node_delete_nic should fail if the node does not exist."""
        with pytest.raises(errors.NotFoundError):
            api.node_delete_nic('compute-01', '01-eth0')

    def test_node_delete_nic_wrong_node(self):
        """node_delete_nic should fail if the nic does not match the node.

        ...even if there is another node that has a nic by that name.
        """
        new_node('compute-01')
        new_node('compute-02')
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(errors.NotFoundError):
            api.node_delete_nic('compute-02', '01-eth0')

    def test_node_delete_nic_wrong_nexist_node(self):
        """Same thing, but with a node that does not exist."""
        new_node('compute-01')
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(errors.NotFoundError):
            api.node_delete_nic('compute-02', '01-eth0')

    def test_node_register_nic_diff_nodes(self):
        """Registering two nics with the same name on diff. nodes is ok."""
        new_node('compute-01')
        new_node('compute-02')
        api.node_register_nic('compute-01', 'ipmi', 'DE:AD:BE:EF:20:14')
        api.node_register_nic('compute-02', 'ipmi', 'DE:AD:BE:EF:20:14')


class TestNodeRegisterDeleteMetadata:
    """Test node_{set,delete}_metadata."""

    pytestmark = pytest.mark.usefixtures(*(default_fixtures +
                                           ['additional_database']))

    def test_node_set_metadata(self):
        """Setting new metadata on a node adds the metadata."""
        api.node_set_metadata('free_node_0', 'EK', 'pk')
        metadata = api._must_find_n(api._must_find(model.Node,
                                                   'free_node_0'),
                                    model.Metadata, 'EK')
        assert metadata.owner.label == 'free_node_0'

    def test_node_update_metadata(self):
        """Updating existing metadata on a node works."""
        api.node_set_metadata('runway_node_0', 'EK', 'new_pk')
        metadata = api._must_find_n(api._must_find(model.Node,
                                                   'runway_node_0'),
                                    model.Metadata, 'EK')
        assert json.loads(metadata.value) == 'new_pk'

    def test_node_set_metadata_no_node(self):
        """Setting metadata on a node that does not exist should fail."""
        with pytest.raises(errors.NotFoundError):
            api.node_set_metadata('compute-01', 'EK', 'pk')

    def test_node_delete_metadata_success(self):
        """Deleting metadata from a node removes that key."""
        api.node_set_metadata('free_node_0', 'EK', 'pk')
        api.node_delete_metadata('free_node_0', 'EK')
        api._assert_absent_n(api._must_find(model.Node,
                                            'free_node_0'),
                             model.Metadata, 'EK')

    def test_node_delete_metadata_metadata_nexist(self):
        """Deleting a metadata key that does not exist fails."""
        with pytest.raises(errors.NotFoundError):
            api.node_delete_metadata('free_node_0', 'EK')

    def test_node_delete_metadata_node_nexist(self):
        """Deleting a metadata key on a node that does not exist fails."""
        with pytest.raises(errors.NotFoundError):
            api.node_delete_metadata('compute-01', 'EK')

    def test_node_delete_metadata_wrong_node(self):
        """Deleting metadata on the wrong node fails."""
        api.node_set_metadata('free_node_0', 'EK', 'pk')
        with pytest.raises(errors.NotFoundError):
            api.node_delete_metadata('free_node_1', 'EK')

    def test_node_delete_metadata_wrong_nexist_node(self):
        """...same thing, but with a node that doesn't exist."""
        api.node_set_metadata('free_node_0', 'EK', 'pk')
        with pytest.raises(errors.NotFoundError):
            api.node_delete_metadata('compute-02', 'EK')

    def test_node_set_metadata_diff_nodes(self):
        """Setting the same metadata key on two different nodes succeeds."""
        api.node_set_metadata('free_node_0', 'EK', 'pk')
        api.node_set_metadata('free_node_1', 'EK', 'pk')

    def test_node_set_metadata_non_string(self):
        """Setting metadata whose value is not just a string works."""
        api.node_set_metadata('free_node_0', 'JSON',
                              {"val1": 1, "val2": 2})


class TestNodeConnectDetachNetwork:
    """Test node_{connect,detach}_network."""

    def test_node_connect_network_success(self, switchinit):
        """Call to node_connect_network adds a NetworkAttachment."""
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', PORTS[2], 'node-99', '99-eth0')

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
        """Connecting a nic that does not exist to a network fails

        ...even if the project has another node with a nic by that name.
        """
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', PORTS[2], 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')
        new_node('node-98')
        api.project_connect_node('anvil-nextgen', 'node-98')   # added

        with pytest.raises(errors.NotFoundError):
            api.node_connect_network('node-98', '99-eth0', 'hammernet')

    def test_node_connect_network_wrong_node_not_in_project(self):
        """...same thing, but with a node that is *not* part that project."""
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        new_node('node-98')

        with pytest.raises(errors.NotFoundError):
            api.node_connect_network('node-98', '99-eth0', 'hammernet')

    def test_node_connect_network_no_such_node(self):
        """Connecting a non-existent nic to a network fails.

        ...even if there is another node with a nic by that name.
        """
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')

        with pytest.raises(errors.NotFoundError):
            api.node_connect_network('node-98', '99-eth0', 'hammernet')  # changed # noqa

    def test_node_connect_network_no_such_nic(self):
        """Connecting a node to a network via a nic it doesn't have fails."""
        new_node('node-99')
#        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')

        with pytest.raises(errors.NotFoundError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')

    def test_node_connect_network_no_such_network(self):
        """Connecting a node to a non-existent network fails."""
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
#        network_create_simple('hammernet', 'anvil-nextgen')
        with pytest.raises(errors.NotFoundError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')

    def test_node_connect_network_node_not_in_project(self):
        """Connecting a node not in a project to a network fails."""
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
#        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')

        with pytest.raises(errors.ProjectMismatchError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')

    def test_node_connect_network_different_projects(self, switchinit):
        """Connecting a node to a network owned by a different project fails.

        (without a specific call to grant access).
        """
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_create('anvil-oldtimer')   # added
        api.project_connect_node('anvil-nextgen', 'node-99')

        network_create_simple('hammernet', 'anvil-oldtimer')  # changed
        api.port_connect_nic('sw0', PORTS[2], 'node-99', '99-eth0')

        with pytest.raises(errors.ProjectMismatchError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')

    def test_node_connect_network_already_attached_to_same(self, switchinit):
        """Connecting a nic to a network twice should fail."""
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')

        api.port_connect_nic('sw0', PORTS[2], 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')  # added
        deferred.apply_networking()  # added

        with pytest.raises(errors.BlockedError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')

    def test_node_connect_network_already_attached_differently(self,
                                                               switchinit):
        """Test connecting a nic that is busy to another network.

        i.e., If the nic is already connected to a different network (on
        the same channel), trying to connect it should fail.
        """
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        network_create_simple('hammernet2', 'anvil-nextgen')  # added
        api.port_connect_nic('sw0', PORTS[2], 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')  # added
        deferred.apply_networking()  # added

        with pytest.raises(errors.BlockedError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet2')

    def test_node_detach_network_success(self, switchinit):
        """Detaching a node from a network removes the NetworkAttachment."""
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', PORTS[2], 'node-99', '99-eth0')
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
        """
        Detaching a node from a network fails, if it isn't attached already.
        """
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
#        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(errors.BadArgumentError):
            api.node_detach_network('node-99', '99-eth0', 'hammernet')

    def test_node_detach_network_wrong_node_in_project(self, switchinit):
        """Detaching the "wrong" node from a network fails.

        In particular, if we have two nodes in a project with nics by the
        same name, with one connected to a network, specifying the wrong
        node name (but right nic and network) will fail.
        """
        new_node('node-99')
        new_node('node-98')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_connect_node('anvil-nextgen', 'node-98')  # added
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', PORTS[2], 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(errors.NotFoundError):
            api.node_detach_network('node-98', '99-eth0', 'hammernet')  # changed  # noqa

    def test_node_detach_network_wrong_node_not_in_project(self, switchinit):
        """Same as above, but the "wrong" node is not part of the project."""
        new_node('node-99')
        new_node('node-98')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', PORTS[2], 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(errors.NotFoundError):
            api.node_detach_network('node-98', '99-eth0', 'hammernet')  # changed  # noqa

    def test_node_detach_network_no_such_node(self, switchinit):
        """Same as above, but the "wrong" node doesn't exist."""
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', PORTS[2], 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(errors.NotFoundError):
            api.node_detach_network('node-98', '99-eth0', 'hammernet')  # changed  # noqa

    def test_node_detach_network_no_such_nic(self, switchinit):
        """Detaching a nic that doesn't exist raises not found."""
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', PORTS[2], 'node-99', '99-eth0')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(errors.NotFoundError):
            api.node_detach_network('node-99', '99-eth1', 'hammernet')  # changed  # noqa

    def test_node_detach_network_node_not_in_project(self, switchinit):
        """Detaching a node that is not in a network fails.

        In particular, this should raise ProjectMismatchError.

        Note that if this is the case, the node should never actually be
        connected to a network; this is mostly checking the ordering of
        the errors.
        """
        new_node('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.project_create('anvil-nextgen')
#        api.project_connect_node('anvil-nextgen', 'node-99')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.port_connect_nic('sw0', PORTS[2], 'node-99', '99-eth0')
#        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(errors.ProjectMismatchError):
            api.node_detach_network('node-99', '99-eth0', 'hammernet')


class TestHeadnodeCreateDelete:
    """Test headnode_{create,delete}"""

    def test_headnode_create_success(self):
        """(successful) call to headnode_create creates the headnode.

        (in the database; this doesn't verify that a VM is actually created).
        """
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        hn = api._must_find(model.Headnode, 'hn-0')
        assert hn.project.label == 'anvil-nextgen'

    def test_headnode_create_badproject(self):
        """Tests that creating a headnode with a nonexistent project fails"""
        with pytest.raises(errors.NotFoundError):
            api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')

    def test_headnode_create_duplicate(self):
        """Tests that creating a headnode with a duplicate name fails"""
        api.project_create('anvil-nextgen')
        api.project_create('anvil-oldtimer')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        with pytest.raises(errors.DuplicateError):
            api.headnode_create('hn-0', 'anvil-oldtimer', 'base-headnode')

    def test_headnode_create_second(self):
        """Tests that creating a second headnode one one project fails"""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create('hn-1', 'anvil-nextgen', 'base-headnode')

    def test_headnode_delete_success(self):
        """headnode_delete removes the object from the database."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_delete('hn-0')
        api._assert_absent(model.Headnode, 'hn-0')

    def test_headnode_delete_nonexistent(self):
        """Tests that deleting a nonexistent headnode fails"""
        with pytest.raises(errors.NotFoundError):
            api.headnode_delete('hn-0')


class TestHeadnodeCreateDeleteHnic:
    """Test headnode_{create,delete}_hnic"""

    def test_headnode_create_hnic_success(self):
        """headnode_create_hnic adds the object to the database."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        nic = api._must_find(model.Hnic, 'hn-0-eth0')
        assert nic.owner.label == 'hn-0'

    def test_headnode_create_hnic_no_headnode(self):
        """Creating an hnic for a non-existent headnode raises not found."""
        with pytest.raises(errors.NotFoundError):
            api.headnode_create_hnic('hn-0', 'hn-0-eth0')

    def test_headnode_create_hnic_duplicate_hnic(self):
        """Creating an hnic that already exists fails."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        with pytest.raises(errors.DuplicateError):
            api.headnode_create_hnic('hn-0', 'hn-0-eth0')

    def test_headnode_delete_hnic_success(self):
        """headnode_delete_hnic removes the Hnic from the database."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        api.headnode_delete_hnic('hn-0', 'hn-0-eth0')
        api._assert_absent(model.Hnic, 'hn-0-eth0')
        api._must_find(model.Headnode, 'hn-0')

    def test_headnode_delete_hnic_hnic_nexist(self):
        """Deleting an hnic that does not exist raises not found."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        with pytest.raises(errors.NotFoundError):
            api.headnode_delete_hnic('hn-0', 'hn-0-eth0')

    def test_headnode_delete_hnic_headnode_nexist(self):
        """
        Deleting an hnic on a headnode that does not exist raises not found.
        """
        with pytest.raises(errors.NotFoundError):
            api.headnode_delete_hnic('hn-0', 'hn-0-eth0')

    def test_headnode_delete_hnic_wrong_headnode(self):
        """Deleting an hnic from the "wrong" headnode fails.

        i.e. if we have an hnic 'hn-0-eth0' scoped to headnode 'hn-0', and
        try to delete it from headnode 'hn-1', this should fail.
        """
        api.project_create('anvil-nextgen')
        api.project_create('anvil-oldtimer')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create('hn-1', 'anvil-oldtimer', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        with pytest.raises(errors.NotFoundError):
            api.headnode_delete_hnic('hn-1', 'hn-0-eth0')

    def test_headnode_delete_hnic_wrong_nexist_headnode(self):
        """Same thing, but when 'hn-1' does not exist."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        with pytest.raises(errors.NotFoundError):
            api.headnode_delete_hnic('hn-1', 'hn-0-eth0')

    def test_headnode_create_hnic_diff_headnodes(self):
        """Creating two hnics by the same name on different headnodes works."""
        api.project_create('anvil-legacy')
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-legacy', 'base-headnode')
        api.headnode_create('hn-1', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'eth0')
        api.headnode_create_hnic('hn-1', 'eth0')


class TestHeadnodeConnectDetachNetwork:
    """Test headnode_{connect,detach}_network."""

    def test_headnode_connect_network_success(self):
        """headnode_connect_network connects the database objects."""
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
        """headnode_connect_network fails if the headnode does not exist."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')

        with pytest.raises(errors.NotFoundError):
            api.headnode_connect_network('hn-1', 'hn-0-eth0', 'hammernet')  # changed  # noqa

    def test_headnode_connect_network_no_such_hnic(self):
        """...or if the hnic does not exist."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')

        with pytest.raises(errors.NotFoundError):
            api.headnode_connect_network('hn-0', 'hn-0-eth1', 'hammernet')  # changed  # noqa

    def test_headnode_connect_network_no_such_network(self):
        """...or if the network does not exist."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')

        with pytest.raises(errors.NotFoundError):
            api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet2')  # changed  # noqa

    def test_headnode_connect_network_already_attached_to_same(self):
        """Connecting an hnic to a network twice is ok.

        This should be idempotent.
        """
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')  # added

        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

    def test_headnode_connect_network_already_attached_differently(self):
        """Connecting an hnic to a network when already on another is ok."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')
        network_create_simple('hammernet2', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')  # added

        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet2')  # changed  # noqa

    def test_headnode_connect_network_different_projects(self):
        """
        Connecting a headnode to a network owned by a different project fails.
        """
        api.project_create('anvil-nextgen')
        api.project_create('anvil-oldtimer')  # added
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-oldtimer')  # changed

        with pytest.raises(errors.ProjectMismatchError):
            api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

    def test_headnode_connect_network_non_allocated(self):
        """Connecting a headnode to a non-allocated network should fail.

        Right now the create_bridges script will only create bridges
        for vlans in the database, so any specified by the administrator
        will not exist. Since the hil does not create the bridges during
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
        with pytest.raises(errors.BadArgumentError):
            api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

    def test_headnode_detach_network_success(self):
        """Detaching a headnode from a network works.

        (in particular, the database is updated correctly).
        """
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
        """
        Detaching a headnode from a network works, even if it is not already
        attached.

        In this case, it's just a noop.
        """
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')
#        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

        api.headnode_detach_network('hn-0', 'hn-0-eth0')

    def test_headnode_detach_network_no_such_headnode(self):
        """Detaching a non-existent headnode raises not found."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

        with pytest.raises(errors.NotFoundError):
            api.headnode_detach_network('hn-1', 'hn-0-eth0')  # changed

    def test_headnode_detach_network_no_such_hnic(self):
        """Detaching a non-existent hnic raises not found."""
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

        with pytest.raises(errors.NotFoundError):
            api.headnode_detach_network('hn-0', 'hn-0-eth1')  # changed


class TestHeadnodeFreeze:
    """Test the "freezing" behavior of headnodes.

    i.e, modifications become illegal once the headnode is started.
    """

    @pytest.fixture(autouse=True)
    def patch_start(self, monkeypatch):
        """Monkeypatch headnode.start for test purposes.

        We can't start the headnodes for real in the test suite, but we need
        "starting" them to still clear the dirty bit.
        """
        def start(self):
            """Set the dirty bit, to mark the headnode as started."""
            self.dirty = False
        monkeypatch.setattr(model.Headnode, 'start', start)

    def _prep(self):
        """Helper to set up common state.

        Creates a project and headnode to work with.
        """
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')

    def _prep_delete_hnic(self):
        """Like _prep, but also creates an hnic that we will delete."""
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
        """Creating an hnic after staring a headnode fails."""
        self._prep()

        api.headnode_start('hn-0')
        with pytest.raises(errors.IllegalStateError):
            api.headnode_create_hnic('hn-0', 'hn-0-eth0')

    def test_succeed_create_hnic(self):
        """Creating an hnic before starting a headnode succeeds."""
        self._prep()

        api.headnode_create_hnic('hn-0', 'hn-0-eth0')

    def test_freeze_fail_delete_hnic(self):
        """Deleting an hnic after starting a headnode fails."""
        self._prep_delete_hnic()

        api.headnode_start('hn-0')
        with pytest.raises(errors.IllegalStateError):
            api.headnode_delete_hnic('hn-0', 'hn-0-eth0')

    def test_succeed_delete_hnic(self):
        """Deleting an hnic before starting a headnode works."""
        self._prep_delete_hnic()

        api.headnode_delete_hnic('hn-0', 'hn-0-eth0')

    def test_freeze_fail_connect_network(self):
        """Connect network fails after starting the headnode."""
        self._prep_connect_network()

        api.headnode_start('hn-0')
        with pytest.raises(errors.IllegalStateError):
            api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

    def test_succeed_connect_network(self):
        """Connect network succeeds before starting the headnode."""
        self._prep_connect_network()

        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

    def test_freeze_fail_detach_network(self):
        """Detach network fails after starting the headnode."""
        self._prep_detach_network()

        api.headnode_start('hn-0')
        with pytest.raises(errors.IllegalStateError):
            api.headnode_detach_network('hn-0', 'hn-0-eth0')

    def test_succeed_detach_network(self):
        """Connect network succeeds after starting the headnode."""
        self._prep_detach_network()

        api.headnode_detach_network('hn-0', 'hn-0-eth0')


class TestNetworkCreateDelete:
    """Tests for the hil.api.network_{create,delete} functions."""

    def test_network_create_success(self):
        """network_create creates the network in the db."""
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        net = api._must_find(model.Network, 'hammernet')
        assert net.owner.label == 'anvil-nextgen'

    def test_network_create_badproject(self):
        """Tests that creating a network with a nonexistent project fails"""
        with pytest.raises(errors.NotFoundError):
            network_create_simple('hammernet', 'anvil-nextgen')

    def test_network_create_duplicate(self):
        """Tests that creating a network with a duplicate name fails"""
        api.project_create('anvil-nextgen')
        api.project_create('anvil-oldtimer')
        network_create_simple('hammernet', 'anvil-nextgen')
        with pytest.raises(errors.DuplicateError):
            network_create_simple('hammernet', 'anvil-oldtimer')

    def test_network_delete_success(self):
        """network_delete removes the network from the db."""
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.network_delete('hammernet')
        api._assert_absent(model.Network, 'hammernet')

    def test_network_delete_project_complex_success(self, switchinit):
        """Do a handful of operations, and make sure nothing explodes.

        In particular, the sequence:

            * add a node to a network
            * remove it
            * delete the network

        should not signal an error.
        """
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:14')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.port_connect_nic('sw0', PORTS[2], 'node-99', 'eth0')
        api.node_connect_network('node-99', 'eth0', 'hammernet')
        deferred.apply_networking()
        api.node_detach_network('node-99', 'eth0', 'hammernet')
        deferred.apply_networking()
        api.network_delete('hammernet')

    def test_network_delete_nonexistent(self):
        """Tests that deleting a nonexistent network fails"""
        with pytest.raises(errors.NotFoundError):
            api.network_delete('hammernet')

    def test_network_delete_node_on_network(self, switchinit):
        """Deleting a node that is attached to a network should fail."""
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.node_register('node-99', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:14')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.port_connect_nic('sw0', PORTS[2], 'node-99', 'eth0')
        api.node_connect_network('node-99', 'eth0', 'hammernet')
        with pytest.raises(errors.BlockedError):
            api.network_delete('hammernet')

    def test_network_delete_headnode_on_network(self):
        """Deleting a headnode that is attached to a network should fail."""
        api.project_create('anvil-nextgen')
        network_create_simple('hammernet', 'anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('hn-0', 'eth0')
        api.headnode_connect_network('hn-0', 'eth0', 'hammernet')
        with pytest.raises(errors.BlockedError):
            api.network_delete('hammernet')


class Test_switch_register:
    """Test switch_register."""

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
        with pytest.raises(errors.DuplicateError):
            api.switch_register('sw0', type=MOCK_SWITCH_TYPE,
                                username="switch_user",
                                password="switch_pass",
                                hostname="switchname")


class Test_switch_delete:
    """Test switch_delete."""

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
        with pytest.raises(errors.NotFoundError):
            api.switch_delete('sw0')


class Test_switch_register_port:
    """Test switch_register_port"""

    def test_register_port(self):
        """Creating a port on an existing switch should succeed."""
        api.switch_register('sw0', type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_register_port('sw0', PORTS[4])
        port = model.Port.query.one()
        assert port.label == PORTS[4]
        assert port.owner.label == 'sw0'

    def test_register_port_nonexisting_switch(self):
        """Creating  port on a non-existent switch should fail."""
        with pytest.raises(errors.NotFoundError):
            api.switch_register_port('sw0', PORTS[4])


class Test_switch_delete_port:
    """Test switch_delete_port"""

    def test_delete_port(self):
        """Removing a port should remove it from the db."""
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_register_port('sw0', PORTS[4])
        api.switch_delete_port('sw0', PORTS[4])
        assert model.Port.query.count() == 0

    def test_delete_port_nonexisting_switch(self):
        """
        Removing a port on a switch that does not exist should
        report the error.
        """
        with pytest.raises(errors.NotFoundError):
            api.switch_delete_port('sw0', PORTS[4])

    def test_delete_port_nonexisting_port(self):
        """Removing a port that does not exist should report the error"""
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        with pytest.raises(errors.NotFoundError):
            api.switch_delete_port('sw0', PORTS[4])


class Test_list_show_switch:
    """Test list_switches/show_switch"""

    def test_list_switches(self):
        """Test list_switches.

        This registers switches, checking the output of list_switches
        beforehand and in between.
        """
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
        """Test show_switch

        This checks the output of show_switch before and after adding a port.
        """
        assert json.loads(api.show_switch('sw0')) == {
            'name': 'sw0',
            'ports': [{'label': PORTS[2]}]
        }

        api.switch_register_port('sw0', PORTS[1])
        # Note: the order of ports is not sorted, test cases need to be in the
        # same order.
        assert json.loads(api.show_switch('sw0')) == {
            'name': 'sw0',
            'ports': [{'label': PORTS[2]},
                      {'label': PORTS[1]}]
        }


class Test_show_port:
    """Test show_port"""

    def test_show_port(self, switchinit):
        """Test show_port

        * Fails on non-existing switch
        * Fails on existent switch & non-existing port
        * Attaching a nic to the port causes the nic's info to show up
          in show_port.
        """
        new_node('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        # call show port on a switch that doesn't exist
        with pytest.raises(errors.NotFoundError):
            api.show_port('non-existing-switch', 'some-port')
        # call show port on a port that's not registered on that switch
        with pytest.raises(errors.NotFoundError):
            api.show_port('sw0', 'non-existing-port')

        assert json.loads(api.show_port('sw0', PORTS[2])) == {}
        # connect the port to a nic, and see if show port agrees
        api.port_connect_nic('sw0', PORTS[2], 'compute-01', 'eth0')
        assert json.loads(api.show_port('sw0', PORTS[2])) == {
                        'node': u'compute-01',
                        'nic': 'eth0',
                        'networks': {}}


class TestPortConnectDetachNic:
    """Test port_{connect,detach}_nic."""

    def test_port_connect_nic_success(self, switchinit):
        """Basic port_connect_nic doesn't raise an error."""
        new_node('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('sw0', PORTS[2], 'compute-01', 'eth0')

    def test_port_connect_nic_no_such_switch(self):
        """Connecting to a non-existent switch raises not found."""
        new_node('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(errors.NotFoundError):
            api.port_connect_nic('sw0', PORTS[2], 'compute-01', 'eth0')

    def test_port_connect_nic_no_such_port(self):
        """Connecting a non-existent port raises not found."""
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        new_node('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(errors.NotFoundError):
            api.port_connect_nic('sw0', PORTS[2], 'compute-01', 'eth0')

    def test_port_connect_nic_no_such_node(self):
        """Connecting a non-existing node raises not found."""
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_register_port('sw0', PORTS[2])
        with pytest.raises(errors.NotFoundError):
            api.port_connect_nic('sw0', PORTS[2], 'compute-01', 'eth0')

    def test_port_connect_nic_no_such_nic(self):
        """Connecting a non-existing nic raises not found."""
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_register_port('sw0', PORTS[2])
        new_node('compute-01')
        with pytest.raises(errors.NotFoundError):
            api.port_connect_nic('sw0', PORTS[2], 'compute-01', 'eth0')

    def test_port_connect_nic_already_attached_to_same(self, switchinit):
        """Connecting a port to a nic twice fails."""
        new_node('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('sw0', PORTS[2], 'compute-01', 'eth0')
        with pytest.raises(errors.DuplicateError):
            api.port_connect_nic('sw0', PORTS[2], 'compute-01', 'eth0')

    def test_port_connect_nic_nic_already_attached_differently(self,
                                                               switchinit):
        """
        Connecting a port to a nic fails, if the nic is attached to another
        port.
        """
        api.switch_register_port('sw0', PORTS[3])
        new_node('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('sw0', PORTS[2], 'compute-01', 'eth0')
        with pytest.raises(errors.DuplicateError):
            api.port_connect_nic('sw0', PORTS[3], 'compute-01', 'eth0')

    def test_port_connect_nic_port_already_attached_differently(self,
                                                                switchinit):
        """
        Connecting a port to a nic fails, if the port is attached to
        another nic.
        """
        new_node('compute-01')
        new_node('compute-02')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.node_register_nic('compute-02', 'eth1', 'DE:AD:BE:EF:20:15')
        api.port_connect_nic('sw0', PORTS[2], 'compute-01', 'eth0')
        with pytest.raises(errors.DuplicateError):
            api.port_connect_nic('sw0', PORTS[2], 'compute-02', 'eth1')

    def test_port_detach_nic_success(self, switchinit):
        """Basic call to port_detach_nic doesn't raise an error."""
        new_node('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('sw0', PORTS[2], 'compute-01', 'eth0')
        api.port_detach_nic('sw0', PORTS[2])

    def test_port_detach_nic_no_such_port(self):
        """Detaching a non-existent port raises not found."""
        with pytest.raises(errors.NotFoundError):
            api.port_detach_nic('sw0', PORTS[2])

    def test_port_detach_nic_not_attached(self):
        """Detaching a port that is not attached fails."""
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_register_port('sw0', PORTS[2])
        new_node('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(errors.NotFoundError):
            api.port_detach_nic('sw0', PORTS[2])

    def port_detach_nic_node_not_free(self, switchinit):
        """should refuse to detach a nic if it has pending actions."""
        new_node('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('sw0', PORTS[2], 'compute-01', 'eth0')

        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'compute-01')

        with pytest.raises(errors.BlockedError):
            api.port_detach_nic('sw0', PORTS[2])


class TestQuery_populated_db:
    """test portions of the query api with a populated database

    Specifically, check against the objects created by ``additional_database.``
    """

    pytestmark = pytest.mark.usefixtures(*(default_fixtures +
                                           ['additional_database']))

    def test_list_networks(self):
        """Test list_networks."""
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
        """
        Attach some nodes to networks, and check list_network_attachments.
        """
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
        """Same thing, but limit the call to a project."""
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
        two show_headnode calls for equality.
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
        """Register some nodes, and check the output of list_nodes('free')."""
        new_node('master-control-program')
        new_node('robocop')
        new_node('data')
        result = json.loads(api.list_nodes("free"))
        # For the lists to be equal, the ordering must be the same:
        result.sort()
        assert result == [
            'data',
            'master-control-program',
            'robocop',
        ]

    def test_list_networks_none(self):
        """list_networks should return an empty list if the db is empty."""
        assert json.loads(api.list_networks()) == {}

    def test_list_projects(self):
        """Add a few projects and check the output of list_projects

        Before, between, and after adding the projects.
        """
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
        """
        list_nodes('free') should return an empty list if the db is empty.
        """
        assert json.loads(api.list_nodes("free")) == []

    def test_some_non_free_nodes(self):
        """Make sure that allocated nodes don't show up in the free list."""
        new_node('master-control-program')
        new_node('robocop')
        new_node('data')

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
        new_node('robocop')
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
                    'port': None,
                    'switch': None,
                    "networks": {}
                },
                {
                    'label': 'wlan0',
                    'macaddr': 'DE:AD:BE:EF:20:15',
                    'port': None,
                    'switch': None,
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

    def test_show_node_free(self):
        """Register a node and show it."""
        new_node('robocop')
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
                    'port': None,
                    'switch': None,
                    "networks": {}
                },
                {
                    'label': 'wlan0',
                    'macaddr': 'DE:AD:BE:EF:20:15',
                    'port': None,
                    'switch': None,
                    "networks": {}
                }
            ],
            'metadata': {}
        }
        self._compare_node_dumps(actual, expected)

    def test_show_node_multiple_network(self):
        """Show a node connected to multiple networks."""
        api.switch_register('sw0',
                            type=MOCK_SWITCH_TYPE,
                            username="switch_user",
                            password="switch_pass",
                            hostname="switchname")
        api.switch_register_port('sw0', PORTS[0])
        api.switch_register_port('sw0', PORTS[1])
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
        api.port_connect_nic('sw0', PORTS[0], 'robocop', 'eth0')
        api.node_connect_network('robocop', 'eth0', 'pxe')
        network_create_simple('storage', 'anvil-nextgen')
        api.port_connect_nic('sw0', PORTS[1], 'robocop', 'wlan0')
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
                    'port': PORTS[0],
                    'switch': 'sw0',
                    "networks": {
                        get_network_allocator().get_default_channel(): 'pxe'
                    }
                },
                {
                    'label': 'wlan0',
                    'macaddr': 'DE:AD:BE:EF:20:15',
                    'port': PORTS[1],
                    'switch': 'sw0',
                    "networks": {
                        get_network_allocator().get_default_channel(): 'storage'  # noqa
                    }
                }
            ],
            'metadata': {}
        }
        self._compare_node_dumps(actual, expected)

    def test_show_nonexistent_node(self):
        """Showing a node that does not exist should raise not found."""
        with pytest.raises(errors.NotFoundError):
            api.show_node('master-control-program')

    def test_project_nodes_exist(self):
        """Test list_project_nodes given a project that has nodes."""
        new_node('master-control-program')
        new_node('robocop')
        new_node('data')

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
        """Test list_project_headnodes given a project with headnodes."""
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
        """Test list_project_nodes on a project with no nodes."""
        api.project_create('anvil-nextgen')
        assert json.loads(api.list_project_nodes('anvil-nextgen')) == []

    def test_no_project_headnodes(self):
        """Test list_project_headnodes on a project with no headnodes."""
        api.project_create('anvil-nextgen')
        assert json.loads(api.list_project_headnodes('anvil-nextgen')) == []

    def test_some_nodes_in_project(self):
        """Test that only assigned nodes are in the project."""
        new_node('master-control-program')
        new_node('robocop')
        new_node('data')

        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'robocop')
        api.project_connect_node('anvil-nextgen', 'data')

        result = json.loads(api.list_project_nodes('anvil-nextgen'))
        result.sort()
        assert result == ['data', 'robocop']

    def test_project_list_networks(self):
        """Test list_project_networks on a project with networks."""
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
        """Test list_project_nodes given a project with no networks."""
        api.project_create('anvil-nextgen')
        assert json.loads(api.list_project_networks('anvil-nextgen')) == []

    def test_show_headnode(self):
        """Create and show a headnode."""
        api.project_create('anvil-nextgen')
        network_create_simple('spiderwebs', 'anvil-nextgen')
        api.headnode_create('BGH', 'anvil-nextgen', 'base-headnode')
        api.headnode_create_hnic('BGH', 'eth0')
        api.headnode_create_hnic('BGH', 'wlan0')
        api.headnode_connect_network('BGH', 'eth0', 'spiderwebs')

        result = json.loads(api.show_headnode('BGH'))

        # Verify UUID is well formed, then delete it, since we can't match it
        # exactly in the check below
        uuid.UUID(result['uuid'])
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

    def test_show_nonexistent_headnode(self):
        """show_headnode on a non-existent headnode should raise not found."""
        with pytest.raises(errors.NotFoundError):
            api.show_headnode('BGH')

    def test_list_headnode_images(self):
        """Test list_headnode_images."""
        result = json.loads(api.list_headnode_images())
        assert result == ['base-headnode', 'img1', 'img2', 'img3', 'img4']


class TestShowNetwork:
    """Test the show_network api cal."""

    def test_show_network_simple(self):
        """Call network_create_simple and show the result."""
        api.project_create('anvil-nextgen')
        network_create_simple('spiderwebs', 'anvil-nextgen')

        result = json.loads(api.show_network('spiderwebs'))
        assert result == {
            'name': 'spiderwebs',
            'owner': 'anvil-nextgen',
            'access': ['anvil-nextgen'],
            "channels": ["vlan/native", "vlan/40"],
            'connected-nodes': {},
        }

    def test_show_network_public(self):
        """show a public network."""
        api.network_create('public-network',
                           owner='admin',
                           access='',
                           net_id='432')

        result = json.loads(api.show_network('public-network'))
        assert result == {
            'name': 'public-network',
            'owner': 'admin',
            'access': None,
            'channels': ['vlan/native', 'vlan/432'],
            'connected-nodes': {},
        }

    def test_show_network_provider(self):
        """show a "provider" network."""
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
            'channels': ['vlan/native', 'vlan/451'],
            'connected-nodes': {},
        }

    def test_show_network_with_nodes(self, switchinit):
        """test the output when a node is connected to a network"""
        auth = get_auth_backend()

        # the following is done by an admin user called 'user'.
        assert auth.get_user() is 'user'
        assert auth.have_admin() is True

        # register a node
        new_node('node-anvil')
        api.node_register_nic('node-anvil', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('sw0', PORTS[2], 'node-anvil', 'eth0')

        # create a project and a network owned by it. Also connect a node to it
        api.project_create('anvil-nextgen')
        api.project_connect_node('anvil-nextgen', 'node-anvil')
        network_create_simple('spiderwebs', 'anvil-nextgen')

        api.node_connect_network('node-anvil', 'eth0', 'spiderwebs')
        deferred.apply_networking()
        result = json.loads(api.show_network('spiderwebs'))

        assert result == {
            'name': 'spiderwebs',
            'owner': 'anvil-nextgen',
            'access': ['anvil-nextgen'],
            "channels": ["vlan/native", "vlan/40"],
            'connected-nodes': {'node-anvil': ['eth0']},
        }

        # register another node
        new_node('node-pineapple')
        api.node_register_nic('node-pineapple', 'eth0', 'DE:AD:BE:EF:20:14')
        api.switch_register_port('sw0', PORTS[1])
        api.port_connect_nic('sw0', PORTS[1], 'node-pineapple', 'eth0')

        # create a new project and give it access to spiderwebs network, and
        # then connect its node to the network.
        api.project_create('pineapple')
        api.network_grant_project_access('pineapple', 'spiderwebs')
        api.project_connect_node('pineapple', 'node-pineapple')

        api.node_connect_network('node-pineapple', 'eth0', 'spiderwebs')
        deferred.apply_networking()

        # switch to a different user and project
        auth.set_user('spongebob')
        project = api._must_find(model.Project, 'pineapple')
        auth.set_project(project)
        auth.set_admin(False)

        result = json.loads(api.show_network('spiderwebs'))

        # check that nodes not owned by this project aren't visible in output.
        assert result == {
            'name': 'spiderwebs',
            'owner': 'anvil-nextgen',
            'access': ['anvil-nextgen', 'pineapple'],
            "channels": ["vlan/native", "vlan/40"],
            'connected-nodes': {'node-pineapple': ['eth0']},
        }

        # switch to the network owner and then see the output

        auth.set_user('user')
        project = api._must_find(model.Project, 'anvil-nextgen')
        auth.set_project(project)
        auth.set_admin(False)

        result = json.loads(api.show_network('spiderwebs'))

        # all nodes should be visible now.
        assert result == {
            'name': 'spiderwebs',
            'owner': 'anvil-nextgen',
            'access': ['anvil-nextgen', 'pineapple'],
            "channels": ["vlan/native", "vlan/40"],
            'connected-nodes': {'node-pineapple': ['eth0'],
                                'node-anvil': ['eth0']},
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
        with pytest.raises(errors.BadArgumentError):
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
                with pytest.raises(errors.BadArgumentError):
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


class TestExtensions:
    """
    Test extension related API calls
    """

    def test_extension_list(self):
        """Test the list_active_extensions api call."""
        result = json.loads(api.list_active_extensions())
        assert result == [
            'hil.ext.auth.mock',
            'hil.ext.network_allocators.vlan_pool',
            'hil.ext.obm.ipmi',
            'hil.ext.obm.mock',
            'hil.ext.switches.mock',
            ]


class TestDryRun:
    """
    Test that api calls using functions with @no_dry_run behave reasonably.
    """

    def test_node_power_cycle(self):
        """Check that power-cycle behaves reasonably under @no_dry_run."""
        api.project_create('anvil-nextgen')
        new_node('node-99')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.node_power_cycle('node-99')

    def test_node_power_cycle_force(self):
        """
        Check that power-cycle with the force flag

        behaves reasonably under @no_dry_run.
        """
        api.project_create('anvil-nextgen')
        new_node('node-99')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.node_power_cycle('node-99', True)
