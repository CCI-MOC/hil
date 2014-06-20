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

    def test_group_connect_project(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen')
        api.group_connect_project('acme-corp', 'anvil-nextgen')
        group = api._must_find(db, model.Group, 'acme-corp')
        project = api._must_find(db, model.Project, 'anvil-nextgen')
        assert project.group is group
        assert project in group.projects
        releaseDB(db)

    def test_group_detach_project(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen')
        api.group_connect_project('acme-corp', 'anvil-nextgen')
        api.group_detach_project('acme-corp', 'anvil-nextgen')
        group = api._must_find(db, model.Group, 'acme-corp')
        project = api._must_find(db, model.Project, 'anvil-nextgen')
        assert project.group is not group
        assert project not in group.projects
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

    def test_duplicate_group_connect_project(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen')
        api.group_connect_project('acme-corp', 'anvil-nextgen')
        with pytest.raises(api.DuplicateError):
            api.group_connect_project('acme-corp', 'anvil-nextgen')
        releaseDB(db)

    def test_bad_group_detach_project(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen')
        with pytest.raises(api.NotFoundError):
            api.group_detach_project('acme-corp', 'anvil-nextgen')
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
        api.project_create('anvil-nextgen')
        api._must_find(db, model.Project, 'anvil-nextgen')
        releaseDB(db)

    def test_project_delete(self):
        db = newDB()
        api.project_create('anvil-nextgen')
        api.project_delete('anvil-nextgen')
        with pytest.raises(api.NotFoundError):
            api._must_find(db, model.Project, 'anvil-nextgen')
        releaseDB(db)

    def test_project_connect_node(self):
        db = newDB()
        api.project_create('anvil-nextgen')
        api.node_register('node-99')
        api.project_connect_node('anvil-nextgen', 'node-99')
        project = api._must_find(db, model.Project, 'anvil-nextgen')
        node = api._must_find(db, model.Node, 'node-99')
        assert node in project.nodes
        assert node.project is project
        releaseDB(db)

    def test_project_detach_node(self):
        db = newDB()
        api.project_create('anvil-nextgen')
        api.node_register('node-99')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_detach_node('anvil-nextgen', 'node-99')
        project = api._must_find(db, model.Project, 'anvil-nextgen')
        node = api._must_find(db, model.Node, 'node-99')
        assert node not in project.nodes
        assert node.project is not project
        releaseDB(db)

    # checks for errors:
    def test_bad_project_detach_node(self):
        """Tests that removing a node from a project it's not in fails."""
        db = newDB()
        api.project_create('anvil-nextgen')
        api.node_register('node-99')
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

    def test_node_delete(self):
        db = newDB()
        api.node_register('node-99')
        api.node_delete('node-99')
        with pytest.raises(api.NotFoundError):
            api._must_find(db, model.Node, 'node-99')
        releaseDB(db)


class TestHeadnode:
    """Tests for the haas.api.node_* functions."""

    def test_headnode_create(self):
        db = newDB()
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api._must_find(db, model.Headnode, 'hn-0')
        releaseDB(db)

    def test_headnode_delete(self):
        db = newDB()
        api.project_create('anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_delete('hn-0')
        with pytest.raises(api.NotFoundError):
            api._must_find(db, model.Headnode, 'hn-0')
