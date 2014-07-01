"""Unit tests for api.py"""

from haas import model, api
from haas.test_common import newDB, releaseDB
import pytest


class TestGroup:
    """Tests for the haas.api.group_* functions."""

    # Several basic tests, functions should succeed in trivial cases.
    def test_group_create(self):
        db = newDB()
        api.group_create('acme-corp')
        api._must_find(db, model.Group, 'acme-corp')
        releaseDB(db)

    def test_group_add_user(self):
        db = newDB()
        api.user_create('alice', 'secret')
        api.group_create('acme-corp')
        api.group_add_user('acme-corp', 'alice')
        user = api._must_find(db, model.User, 'alice')
        group = api._must_find(db, model.Group, 'acme-corp')
        assert group in user.groups
        assert user in group.users
        releaseDB(db)

    def test_group_remove_user(self):
        db = newDB()
        api.user_create('alice', 'secret')
        api.group_create('acme-corp')
        api.group_add_user('acme-corp', 'alice')
        api.group_remove_user('acme-corp', 'alice')
        user = api._must_find(db, model.User, 'alice')
        group = api._must_find(db, model.Group, 'acme-corp')
        assert group not in user.groups
        assert user not in group.users
        releaseDB(db)

    def test_group_delete(self):
        db = newDB()
        api.group_create('acme-corp')
        api.group_delete('acme-corp')
        with pytest.raises(api.NotFoundError):
            api._must_find(db, model.Group, 'acme-corp')
        releaseDB(db)

    # Error handling tests:
    def test_duplicate_group_create(self):
        db = newDB()
        api.group_create('acme-corp')
        with pytest.raises(api.DuplicateError):
            api.group_create('acme-corp')
        releaseDB(db)

    def test_duplicate_group_add_user(self):
        db = newDB()
        api.user_create('alice', 'secret')
        api.group_create('acme-corp')
        api.group_add_user('acme-corp', 'alice')
        with pytest.raises(api.DuplicateError):
            api.group_add_user('acme-corp', 'alice')
        releaseDB(db)

    def test_bad_group_remove_user(self):
        """Tests that removing a user from a group they're not in fails."""
        db = newDB()
        api.user_create('alice', 'secret')
        api.group_create('acme-corp')
        with pytest.raises(api.NotFoundError):
            api.group_remove_user('acme-corp', 'alice')
        releaseDB(db)

class TestUser:
    """Tests for the haas.api.user_* functions."""

    def test_new_user(self):
        db = newDB()
        api._assert_absent(db, model.User, 'bob')
        api.user_create('bob', 'foo')
        releaseDB(db)

    def test_duplicate_user(self):
        db = newDB()
        api.user_create('alice', 'secret')
        with pytest.raises(api.DuplicateError):
                api.user_create('alice', 'password')
        releaseDB(db)

    def test_delete_user(self):
        db = newDB()
        api.user_create('bob', 'foo')
        api.user_delete('bob')
        releaseDB(db)

    def test_delete_missing_user(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.user_delete('bob')
        releaseDB(db)

    def test_delete_user_twice(self):
        db = newDB()
        api.user_create('bob', 'foo')
        api.user_delete('bob')
        with pytest.raises(api.NotFoundError):
            api.user_delete('bob')
        releaseDB(db)


class TestProject:
    """Tests for the haas.api.project_* functions."""

    def test_project_create(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        api._must_find(db, model.Project, 'anvil-nextgen')
        releaseDB(db)

    def test_project_delete(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        api.project_delete('anvil-nextgen')
        with pytest.raises(api.NotFoundError):
            api._must_find(db, model.Project, 'anvil-nextgen')
        releaseDB(db)

    def test_project_connect_node(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        api.node_register('node-99')
        api.project_connect_node('anvil-nextgen', 'node-99')
        project = api._must_find(db, model.Project, 'anvil-nextgen')
        node = api._must_find(db, model.Node, 'node-99')
        assert node in project.nodes
        assert node.project is project
        releaseDB(db)

    def test_project_connect_node_project_nexist(self):
        """Tests that connecting a node to a nonexistent project fails"""
        db = newDB()
        api.node_register('node-99')
        with pytest.raises(api.NotFoundError):
            api.project_connect_node('anvil-nextgen', 'node-99')
        releaseDB(db)

    def test_project_connect_node_node_nexist(self):
        """Tests that connecting a nonexistent node to a projcet fails"""
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        with pytest.raises(api.NotFoundError):
            api.project_connect_node('anvil-nextgen', 'node-99')
        releaseDB(db)

    def test_project_detach_node(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        api.node_register('node-99')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_detach_node('anvil-nextgen', 'node-99')
        project = api._must_find(db, model.Project, 'anvil-nextgen')
        node = api._must_find(db, model.Node, 'node-99')
        assert node not in project.nodes
        assert node.project is not project
        releaseDB(db)

    def test_project_detach_node_notattached(self):
        """Tests that removing a node from a project it's not in fails."""
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        api.node_register('node-99')
        with pytest.raises(api.NotFoundError):
            api.project_detach_node('anvil-nextgen', 'node-99')
        releaseDB(db)

    def test_project_detach_node_project_nexist(self):
        """Tests that removing a node from a nonexistent project fails."""
        db = newDB()
        api.node_register('node-99')
        with pytest.raises(api.NotFoundError):
            api.project_detach_node('anvil-nextgen', 'node-99')
        releaseDB(db)

    def test_project_detach_node_node_nexist(self):
        """Tests that removing a nonexistent node from a project fails."""
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        with pytest.raises(api.NotFoundError):
            api.project_detach_node('anvil-nextgen', 'node-99')
        releaseDB(db)


class TestNode:
    """Tests for the haas.api.node_* functions."""

    def test_node_register(self):
        db = newDB()
        api.node_register('node-99')
        api._must_find(db, model.Node, 'node-99')
        releaseDB(db)

    def test_duplicate_node_register(self):
        db = newDB()
        api.node_register('node-99')
        with pytest.raises(api.DuplicateError):
            api.node_register('node-99')
        releaseDB(db)

    def test_node_delete(self):
        db = newDB()
        api.node_register('node-99')
        api.node_delete('node-99')
        with pytest.raises(api.NotFoundError):
            api._must_find(db, model.Node, 'node-99')
        releaseDB(db)


class TestHeadnode:
    """Tests for the haas.api.node_* functions."""

    def test_headnode_create_success(self):
        db = newDB()
        api.group_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen')
        hn = api._must_find(db, model.Headnode, 'hn-0')
        assert hn.group.label == 'anvil-nextgen'
        releaseDB(db)

    def test_headnode_create_badgroup(self):
        """Tests that creating a headnode with a nonexistent group fails"""
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.headnode_create('hn-0', 'anvil-nextgen')
        releaseDB(db)

    def test_headnode_create_duplicate(self):
        """Tests that creating a headnode with a duplicate name fails"""
        db = newDB()
        api.group_create('anvil-nextgen')
        api.group_create('anvil-oldtimer')
        api.headnode_create('hn-0', 'anvil-nextgen')
        with pytest.raises(api.DuplicateError):
            api.headnode_create('hn-0', 'anvil-oldtimer')
        releaseDB(db)

    def test_headnode_delete_success(self):
        db = newDB()
        api.group_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_delete('hn-0')
        api._assert_absent(db, model.Headnode, 'hn-0')
        releaseDB(db)

    def test_headnode_delete_nonexistent(self):
        """Tests that deleting a nonexistent headnode fails"""
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.headnode_delete('hn-0')
        releaseDB(db)


    def test_headnode_create_hnic_success(self):
        db = newDB()
        api.group_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        nic = api._must_find(db, model.Hnic, 'hn-0-eth0')
        assert nic.headnode.label == 'hn-0'
        assert nic.group.label == 'anvil-nextgen'
        releaseDB(db)

    def test_headnode_create_hnic_no_headnode(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        releaseDB(db)

    def test_headnode_create_hnic_duplicate_hnic(self):
        db = newDB()
        api.group_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.DuplicateError):
            api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:15')
        releaseDB(db)

    def test_headnode_delete_hnic_success(self):
        db = newDB()
        api.group_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        api.headnode_delete_hnic('hn-0', 'hn-0-eth0')
        api._assert_absent(db, model.Hnic, 'hn-0-eth0')
        hn = api._must_find(db, model.Headnode, 'hn-0')
        releaseDB(db)

    def test_headnode_delete_hnic_hnic_nexist(self):
        db = newDB()
        api.group_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen')
        with pytest.raises(api.NotFoundError):
            api.headnode_delete_hnic('hn-0', 'hn-0-eth0')
        releaseDB(db)

    def test_headnode_delete_hnic_headnode_nexist(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.headnode_delete_hnic('hn-0', 'hn-0-eth0')
        releaseDB(db)

    def test_headnode_delete_hnic_wrong_headnode(self):
        db = newDB()
        api.group_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create('hn-1', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.headnode_delete_hnic('hn-1', 'hn-0-eth0')
        releaseDB(db)

    def test_headnode_delete_hnic_wrong_nexist_headnode(self):
        db = newDB()
        api.group_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.headnode_delete_hnic('hn-1', 'hn-0-eth0')
        releaseDB(db)


class TestNetwork:
    """Tests for the haas.api.network_* functions."""

    def test_network_create_success(self):
        db = newDB()
        api.vlan_register('102')
        api.group_create('anvil-nextgen')
        api.network_create('hammernet', 'anvil-nextgen')
        net = api._must_find(db, model.Network, 'hammernet')
        assert net.group.label == 'anvil-nextgen'
        vlan = api._must_find(db, model.Vlan, '102')
        assert not vlan.available
        releaseDB(db)

    def test_network_create_badgroup(self):
        """Tests that creating a network with a nonexistent group fails"""
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.network_create('hammernet', 'anvil-nextgen')
        releaseDB(db)

    def test_network_create_duplicate(self):
        """Tests that creating a network with a duplicate name fails"""
        db = newDB()
        api.vlan_register('102')
        api.group_create('anvil-nextgen')
        api.group_create('anvil-oldtimer')
        api.network_create('hammernet', 'anvil-nextgen')
        with pytest.raises(api.DuplicateError):
            api.network_create('hammernet', 'anvil-oldtimer')
        releaseDB(db)

    def test_network_delete_success(self):
        db = newDB()
        api.vlan_register('102')
        api.group_create('anvil-nextgen')
        api.network_create('hammernet', 'anvil-nextgen')
        api.network_delete('hammernet')
        api._assert_absent(db, model.Network, 'hammernet')
        vlan = api._must_find(db, model.Vlan, '102')
        assert vlan.available
        releaseDB(db)

    def test_network_delete_nonexistent(self):
        """Tests that deleting a nonexistent network fails"""
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.network_delete('hammernet')
        releaseDB(db)

    def test_network_basic_vlan_leak(self):
        db = newDB()
        api.group_create('acme_corp')
        api.vlan_register('102')
        api.network_create('hammernet', 'acme_corp')
        api.network_delete('hammernet')
        # For this to work, the vlan will need to have been released:
        api.network_create('sledge', 'acme_corp')
        releaseDB(db)

    def test_network_no_duplicates(self):
        db = newDB()
        api.group_create('acme_corp')
        api.vlan_register('102')
        api.network_create('hammernet', 'acme_corp')
        with pytest.raises(api.AllocationError):
            api.network_create('sledge', 'acme_corp')
        releaseDB(db)

class TestVlan:

    def test_vlan_register_success(self):
        db = newDB()
        api.vlan_register('102')
        vlan = api._must_find(db, model.Vlan, '102')
        assert vlan.vlan_no == 102
        assert vlan.available
        releaseDB(db)

    def test_vlan_register_bad_number(self):
        """Test various bad inputs."""
        db = newDB()
        inputs = ['5000', 'aleph0', '4.2', '-21', 'PI', 'infinity', 'NaN']
        for input in inputs:
            with pytest.raises(api.BadArgumentError):
                api.vlan_register(input)
        releaseDB(db)

    def test_duplicate_vlan_register(self):
        db = newDB()
        api.vlan_register('102')
        with pytest.raises(api.DuplicateError):
            api.vlan_register('102')
