from haas import api, model, config, server
from haas.test_common import config_testsuite, config_merge, fresh_database
from haas.rest import RequestContext
from haas.ext.auth.database import User, user_create, user_delete, \
    project_add_user, project_remove_user
import pytest


@pytest.fixture
def configure():
    config_testsuite()
    config_merge({
        'extensions': {
            'haas.ext.auth.database': '',
        },
    })
    config.load_extensions()


@pytest.fixture
def db(request):
    return fresh_database(request)


@pytest.fixture
def server_init():
    server.register_drivers()
    server.validate_state()


@pytest.yield_fixture
def with_request_context():
    with RequestContext():
        yield


pytestmark = pytest.mark.usefixtures('configure',
                                     'db',
                                     'server_init',
                                     'with_request_context')


class TestUser:
    """Tests for the haas.api.user_* functions."""

    def test_new_user(self):
        api._assert_absent(User, 'bob')
        user_create('bob', 'foo')

    def test_duplicate_user(self):
        user_create('alice', 'secret')
        with pytest.raises(api.DuplicateError):
                user_create('alice', 'password')

    def test_delete_user(self):
        user_create('bob', 'foo')
        user_delete('bob')

    def test_delete_missing_user(self):
        with pytest.raises(api.NotFoundError):
            user_delete('bob')

    def test_delete_user_twice(self):
        user_create('bob', 'foo')
        user_delete('bob')
        with pytest.raises(api.NotFoundError):
            user_delete('bob')


class TestProjectAddDeleteUser:
    """Tests for adding and deleting a user from a project"""

    def test_project_add_user(self, db):
        user_create('alice', 'secret')
        api.project_create('acme-corp')
        project_add_user('acme-corp', 'alice')
        user = api._must_find(User, 'alice')
        project = api._must_find(model.Project, 'acme-corp')
        assert project in user.projects
        assert user in project.users

    def test_project_remove_user(self, db):
        user_create('alice', 'secret')
        api.project_create('acme-corp')
        project_add_user('acme-corp', 'alice')
        project_remove_user('acme-corp', 'alice')
        user = api._must_find(User, 'alice')
        project = api._must_find(model.Project, 'acme-corp')
        assert project not in user.projects
        assert user not in project.users

    def test_duplicate_project_add_user(self, db):
        user_create('alice', 'secret')
        api.project_create('acme-corp')
        project_add_user('acme-corp', 'alice')
        with pytest.raises(api.DuplicateError):
            project_add_user('acme-corp', 'alice')

    def test_bad_project_remove_user(self, db):
        """Tests that removing a user from a project they're not in fails."""
        user_create('alice', 'secret')
        api.project_create('acme-corp')
        with pytest.raises(api.NotFoundError):
            project_remove_user('acme-corp', 'alice')
