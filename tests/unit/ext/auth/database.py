from haas import api, model, config, server
from haas.test_common import config_testsuite, config_merge, fresh_database, \
    ModelTest
from haas.errors import AuthorizationError
from haas.rest import RequestContext, local
from haas.ext.auth.database import User, user_create, user_delete, \
    project_add_user, project_remove_user
import pytest
import unittest


@pytest.fixture
def configure():
    config_testsuite()
    config_merge({
        'extensions': {
            'haas.ext.auth.database': '',
            'haas.ext.auth.null': None,
        },
    })
    config.load_extensions()


@pytest.fixture
def db(request):
    session = fresh_database(request)
    alice = User(label='alice',
                 password='secret',
                 is_admin=True)
    bob = User(label='bob',
               password='password',
               is_admin=False)

    session.add(alice)
    session.add(bob)

    runway = model.Project('runway')
    runway.users.append(alice)
    session.add(runway)
    session.commit()

    return session


@pytest.fixture
def server_init():
    server.register_drivers()
    server.validate_state()


@pytest.yield_fixture
def with_request_context():
    with RequestContext():
        yield


class FakeAuthRequest(object):
    """Fake (authenticated) request object.

    This spoofs just enough of werkzeug's request functionality for the
    database auth plugin to work.
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def authorization(self):
        return self


@pytest.fixture
def admin_auth():
    """Inject mock credentials that give the request admin access."""
    local.request = FakeAuthRequest('alice', 'secret')


@pytest.fixture
def runway_auth():
    """Inject mock credentials that give the request access to the "runway" project."""
    local.request = FakeAuthRequest('bob', 'password')



def use_fixtures(auth_fixture):
    return pytest.mark.usefixtures('configure',
                                   'db',
                                   'server_init',
                                   auth_fixture,
                                   'with_request_context')


@use_fixtures('admin_auth')
class TestUser(unittest.TestCase):
    """Tests for the haas.api.user_* functions."""

    def test_new_user(self):
        api._assert_absent(User, 'charlie')
        user_create('charlie', 'foo')

    def test_duplicate_user(self):
        user_create('charlie', 'secret')
        with pytest.raises(api.DuplicateError):
                user_create('charlie', 'password')

    def test_delete_user(self):
        user_create('charlie', 'foo')
        user_delete('charlie')

    def test_delete_missing_user(self):
        with pytest.raises(api.NotFoundError):
            user_delete('charlie')

    def test_delete_user_twice(self):
        user_create('charlie', 'foo')
        user_delete('charlie')
        with pytest.raises(api.NotFoundError):
            user_delete('charlie')


@use_fixtures('admin_auth')
class TestProjectAddDeleteUser(unittest.TestCase):
    """Tests for adding and deleting a user from a project"""

    def test_project_add_user(self):
        user_create('charlie', 'secret')
        api.project_create('acme-corp')
        project_add_user('acme-corp', 'charlie')
        user = api._must_find(User, 'charlie')
        project = api._must_find(model.Project, 'acme-corp')
        assert project in user.projects
        assert user in project.users

    def test_project_remove_user(self):
        user_create('charlie', 'secret')
        api.project_create('acme-corp')
        project_add_user('acme-corp', 'charlie')
        project_remove_user('acme-corp', 'charlie')
        user = api._must_find(User, 'charlie')
        project = api._must_find(model.Project, 'acme-corp')
        assert project not in user.projects
        assert user not in project.users

    def test_duplicate_project_add_user(self):
        user_create('charlie', 'secret')
        api.project_create('acme-corp')
        project_add_user('acme-corp', 'charlie')
        with pytest.raises(api.DuplicateError):
            project_add_user('acme-corp', 'charlie')

    def test_bad_project_remove_user(self):
        """Tests that removing a user from a project they're not in fails."""
        user_create('charlie', 'secret')
        api.project_create('acme-corp')
        with pytest.raises(api.NotFoundError):
            project_remove_user('acme-corp', 'charlie')


@pytest.mark.usefixtures('configure', 'db')
class TestUsers(ModelTest):
    """Test user-related functionality"""

    def sample_obj(self):
        return User('charlie', 'secret')


admin_calls = [
    (user_create, ['charlie', '1337']),
    (user_create, ['charlie', '1337', False]),
    (user_create, ['charlie', '1337', True]),
    (user_delete, ['bob']),
    (project_add_user, ['runway', 'bob']),
    (project_remove_user, ['runway', 'alice']),
]


@pytest.mark.parametrize('fn,args', admin_calls)
@use_fixtures('admin_auth')
def test_admin_succeed(fn, args):
    fn(*args)


@pytest.mark.parametrize('fn,args', admin_calls)
@use_fixtures('runway_auth')
def test_admin_fail(fn, args):
    with pytest.raises(AuthorizationError):
        fn(*args)
