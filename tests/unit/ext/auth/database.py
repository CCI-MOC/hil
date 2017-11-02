"""Test the database auth backend."""
from hil import api, model, config, errors
from hil.test_common import config_testsuite, config_merge, fresh_database, \
    ModelTest, fail_on_log_warnings, server_init
from hil.flaskapp import app
from hil.model import db
from hil.rest import init_auth, local
import flask
import pytest
import unittest

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)
server_init = pytest.fixture(server_init)


@pytest.fixture
def dbauth():
    """Fixture returing hil.ext.auth.database

    This is useful because we can't import it at top level, so this lets us
    still refer to it by a single expression.
    """
    from hil.ext.auth import database
    return database


class DBAuthTestCase(unittest.TestCase):
    """Superclass for ``TestCase``s which use the dbauth() fixture.

    This just calls the fixture once, and stores its result in self.
    """

    def setUp(self):
        self.dbauth = dbauth()


@pytest.fixture
def configure():
    """Configure HIL."""
    config_testsuite()
    config_merge({
        'auth': {
            # The tests in this module are checking the specific authorization
            # requirements of the API calls. as such, we don't want things to
            # fail due to complete lack of authentication, where they should
            # fail later when the specific authorization checks we're testing
            # for happen.
            'require_authentication': 'False',
        },
        'extensions': {
            'hil.ext.auth.database': '',
            'hil.ext.auth.null': None,
        },
    })
    config.load_extensions()


@pytest.fixture
def initial_db(request, dbauth):
    """Populate the database with an initial set of objects.

    Just a few users & projects.
    """
    fresh_database(request)
    with app.app_context():
        alice = dbauth.User(label='alice',
                            password='secret',
                            is_admin=True)
        bob = dbauth.User(label='bob',
                          password='password',
                          is_admin=False)

        db.session.add(alice)
        db.session.add(bob)

        runway = model.Project('runway')
        runway.users.append(alice)
        db.session.add(runway)
        db.session.commit()


@pytest.yield_fixture
def auth_context():
    """Run the test in a request context, after calling init_auth."""
    with app.test_request_context():
        init_auth()
        yield


class FakeAuthRequest(object):
    """Fake (authenticated) request object.

    This spoofs just enough of flask's request functionality for the
    database auth plugin to work.
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password

    @property
    def authorization(self):
        """Spoof the 'authorization' property.

        We just return 'self' for this, since we already have the username &
        password properties.
        """
        return self


class FakeNoAuthRequest(object):
    """Fake (unauthenticated) request object.

    Like `FakeAuthRequest`, except that the spoofed request is
    unauthenticated.
    """
    authorization = None


@pytest.fixture
def admin_auth():
    """Inject mock credentials that give the request admin access."""
    flask.request = FakeAuthRequest('alice', 'secret')


@pytest.fixture
def runway_auth():
    """
    Inject mock credentials that give the request
    access to the "runway" project.
    """
    flask.request = FakeAuthRequest('bob', 'password')


@pytest.fixture
def no_auth():
    """Spoof an unauthenticated request."""
    flask.request = FakeNoAuthRequest()


def use_fixtures(auth_fixture):
    """Load standard fixtures + auth_fixture.

    auth_fixture is the name of a fixture used to authenticate the request,
    e.g. 'admin_auth', 'runway_auth'...

    This is useful since most of our tests use the same set of fixtures, but
    test different levels of authorization/authentication
    """
    return pytest.mark.usefixtures('configure',
                                   'initial_db',
                                   'server_init',
                                   auth_fixture,
                                   'auth_context')


@use_fixtures('admin_auth')
class TestUserCreateDelete(DBAuthTestCase):
    """Tests for user_create and user_delete."""

    def setUp(self):
        from hil.ext.auth import database as dbauth
        self.dbauth = dbauth

    def test_new_user(self):
        """Creating a (previously absent) user should succeed."""
        api._assert_absent(self.dbauth.User, 'charlie')
        self.dbauth.user_create('charlie', 'foo')

    def test_duplicate_user(self):
        """Creating a user that already exists should fail."""
        self.dbauth.user_create('charlie', 'secret')
        with pytest.raises(errors.DuplicateError):
            self.dbauth.user_create('charlie', 'password')

    def test_delete_user(self):
        """Try creating and deleting a user.

        Requests should succeed.
        """
        self.dbauth.user_create('charlie', 'foo')
        self.dbauth.user_delete('charlie')

    def test_delete_missing_user(self):
        """Test that deleting a missing user raises not found."""
        with pytest.raises(errors.NotFoundError):
            self.dbauth.user_delete('charlie')

    def test_delete_user_twice(self):
        """Test that deleting a user twice raises not found."""
        self.dbauth.user_create('charlie', 'foo')
        self.dbauth.user_delete('charlie')
        with pytest.raises(errors.NotFoundError):
            self.dbauth.user_delete('charlie')

    def _new_user(self, is_admin):
        """Helper method for creating/switching to a new user.

        A new admin user will be created with the credentials:

        username: 'charlie'
        password: 'foo'

        The argument is_admin determines whether the user has admin rights.

        Once the user has been created, the authentication info will be
        changed to that user.
        """
        self.dbauth.user_create('charlie', 'foo', is_admin=is_admin)
        flask.request = FakeAuthRequest('charlie', 'foo')
        local.auth = self.dbauth.User.query.filter_by(label='charlie').one()

    def test_new_admin_can_admin(self):
        """Verify that a newly created admin can actually do admin stuff."""
        self._new_user(is_admin=True)
        self.dbauth.user_delete('charlie')

    def test_new_non_admin_cannot_admin(self):
        """Verify that a newly created regular user can't do admin stuff."""
        self._new_user(is_admin=False)
        with pytest.raises(errors.AuthorizationError):
            self.dbauth.user_delete('charlie')


@use_fixtures('admin_auth')
class TestUserSetAdmin(DBAuthTestCase):
    """Tests for user_set_admin."""

    def setUp(self):
        from hil.ext.auth import database as dbauth
        self.dbauth = dbauth

    def _new_user(self, is_admin):
        """Helper method for creating/switching to a new user.

        A new admin user will be created with the credentials:

        username: 'charlie'
        password: 'foo'

        The argument is_admin determines whether the user has admin rights.

        Once the user has been created, the authentication info will be
        changed to that user.
        """
        self.dbauth.user_create('charlie', 'foo', is_admin=is_admin)
        flask.request = FakeAuthRequest('charlie', 'foo')
        local.auth = self.dbauth.User.query.filter_by(label='charlie').one()

    def test_user_set_admin(self):
        """Try promoting and demoting users.

        This just checks that the api calls "succeed" in the sense of not
        throwing returning errors.
        """
        self.dbauth.user_create('charlie', 'foo', False)
        self.dbauth.user_set_admin('charlie', True)
        self.dbauth.user_delete('charlie')
        self.dbauth.user_create('charlie', 'foo', True)
        self.dbauth.user_set_admin('charlie', False)
        self.dbauth.user_delete('charlie')

    def test_mod_admin_can_admin(self):
        """Verify that a newly promoted admin can actually do admin stuff."""
        self.dbauth.user_create('charlie', 'foo', False)
        self.dbauth.user_set_admin('charlie', True)
        flask.request = FakeAuthRequest('charlie', 'foo')
        local.auth = self.dbauth.User.query.filter_by(label='charlie').one()
        self.dbauth.user_delete('charlie')

    def test_mod_non_admin_cannot_admin(self):
        """Verify that a newly demoted regular user can't do admin stuff."""
        self.dbauth.user_create('charlie', 'foo', True)
        self.dbauth.user_set_admin('charlie', False)
        flask.request = FakeAuthRequest('charlie', 'foo')
        local.auth = self.dbauth.User.query.filter_by(label='charlie').one()
        with pytest.raises(errors.AuthorizationError):
            self.dbauth.user_delete('charlie')

    def test_user_cannot_self_promote(self):
        """Verify that a user cannot self-promote to admin."""
        self._new_user(is_admin=False)
        with pytest.raises(errors.AuthorizationError):
            self.dbauth.user_set_admin('charlie', True)

    def test_user_cannot_self_demote(self):
        """Verify that a user cannot self-demote to regular."""
        self._new_user(is_admin=True)
        with pytest.raises(errors.IllegalStateError):
            self.dbauth.user_set_admin('charlie', False)


@use_fixtures('admin_auth')
class TestUserAddRemoveProject(DBAuthTestCase):
    """Tests for user_add_project/user_remove_project."""

    def test_user_add_project(self):
        """Test that user_add_project correctly adds the user."""
        self.dbauth.user_create('charlie', 'secret')
        api.project_create('acme-corp')
        self.dbauth.user_add_project('charlie', 'acme-corp')
        user = api._must_find(self.dbauth.User, 'charlie')
        project = api._must_find(model.Project, 'acme-corp')
        assert project in user.projects
        assert user in project.users

    def test_user_remove_project(self):
        """Test that user_remove_project correctly removes the user."""
        self.dbauth.user_create('charlie', 'secret')
        api.project_create('acme-corp')
        self.dbauth.user_add_project('charlie', 'acme-corp')
        self.dbauth.user_remove_project('charlie', 'acme-corp')
        user = api._must_find(self.dbauth.User, 'charlie')
        project = api._must_find(model.Project, 'acme-corp')
        assert project not in user.projects
        assert user not in project.users

    def test_duplicate_user_add_project(self):
        """Test that adding a user that already exists fails."""
        self.dbauth.user_create('charlie', 'secret')
        api.project_create('acme-corp')
        self.dbauth.user_add_project('charlie', 'acme-corp')
        with pytest.raises(errors.DuplicateError):
            self.dbauth.user_add_project('charlie', 'acme-corp')

    def test_bad_user_remove_project(self):
        """Tests that removing a user from a project they're not in fails."""
        self.dbauth.user_create('charlie', 'secret')
        api.project_create('acme-corp')
        with pytest.raises(errors.NotFoundError):
            self.dbauth.user_remove_project('charlie', 'acme-corp')


@pytest.mark.usefixtures('configure', 'initial_db')
class TestUserModel(ModelTest):
    """Basic sanity check for the User model.

    Similar to the tests in /tests/unit/model.py, which cover the models
    defined in HIL core.
    """

    def sample_obj(self):
        return dbauth().User('charlie', 'secret')


admin_calls = [
    ('user_create', ['charlie', '1337']),
    ('user_create', ['charlie', '1337', False]),
    ('user_create', ['charlie', '1337', True]),
    ('user_delete', ['bob']),
    ('user_add_project', ['bob', 'runway']),
    ('user_remove_project', ['alice', 'runway']),
]


@pytest.mark.parametrize('fn,args', admin_calls)
@use_fixtures('admin_auth')
def test_admin_succeed(fn, args):
    """Verify that an admin-only call succeds when invoked by an admin."""
    from hil.ext.auth import database as dbauth
    fn = getattr(dbauth, fn)
    fn(*args)


@pytest.mark.parametrize('fn,args', admin_calls)
@use_fixtures('runway_auth')
def test_admin_runway_fail(fn, args):
    """
    Verify that an admin-only call fails when invoked by a non-admin user.
    """
    from hil.ext.auth import database as dbauth
    fn = getattr(dbauth, fn)
    with pytest.raises(errors.AuthorizationError):
        fn(*args)


@pytest.mark.parametrize('fn,args', admin_calls)
@use_fixtures('no_auth')
def test_admin_noauth_fail(fn, args):
    """
    Verify that an admin-only call fails when invoked without authentication.
    """
    from hil.ext.auth import database as dbauth
    fn = getattr(dbauth, fn)
    with pytest.raises(errors.AuthorizationError):
        fn(*args)
