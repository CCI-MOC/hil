"""Tests for the keystone auth backend.

Note that these require a keystone instance to be installed and running, with
a specific configuration and database contents. The script
"ci/keystone/keystone.sh" at the root of the repository can be used to set
this up. This is done automatically in our travis config.
"""
from haas import test_common as tc
from haas.test_common import fail_on_log_warnings
from haas import server, config, model, rest, auth
from haas.flaskapp import app
import pytest
import requests
import time
from schema import Schema
from threading import Thread

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneauth1.exceptions.http import HttpError
from keystoneclient import client

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


# A list of projects to be added to HaaS's database.
project_db = ['admin', 'service']


# A list of users to use in the tests below.
user_db = [
    {
        'name': 'admin',
        'password': 's3cr3t',
        'project_name': 'admin',
        'admin': True,
    },
    {
        'name': 'nova',
        'password': 'nova',
        'project_name': 'service',
        'admin': False,
    },
]


def _keystone_cfg_opt(name):
    """Get the value of the keystone auth backend's `name` option.

    i.e. that option in the extension's section of the config file.
    """
    return config.cfg.get('haas.ext.auth.keystone', name)


def _get_keystone_session(username, password, project_name):
    """Return a keystone `Session` obect for the given user/project.

    username, password and project_name are the keystone user/pass/project
    of the desired session.
    """

    auth = v3.Password(auth_url=_keystone_cfg_opt('auth_url'),
                       username=username,
                       password=password,
                       project_name=project_name,
                       user_domain_id='default',
                       project_domain_id='default')
    return session.Session(auth=auth)


@pytest.fixture
def configure():
    """Fixture which setups up haas.cfg, and loads extensions and such."""
    tc.config_testsuite()
    tc.config_merge({
        'extensions': {
            'haas.ext.auth.null': None,
            'haas.ext.auth.keystone': '',
        },
        'haas.ext.auth.keystone': {
            'auth_url': 'http://127.0.0.1:35357/v3',
            'auth_protocol': 'http',
            'username': 'admin',
            'password': 's3cr3t',
            'project_name': 'admin',
            'admin_user': 'admin',
            'admin_password': 's3cr3t',
        },
    })
    # the keystone client library actually bombs out if we don't configure
    # logging:
    config.configure_logging()
    config.load_extensions()


fresh_database = pytest.fixture(tc.fresh_database)


@pytest.fixture
def keystone_session():
    """Return a keystone Session from the options in haas.cfg"""

    return _get_keystone_session(
        username=_keystone_cfg_opt('username'),
        password=_keystone_cfg_opt('password'),
        project_name=_keystone_cfg_opt('project_name'),
    )


@pytest.fixture
def keystone_client(keystone_session):
    """Return a keystone client from the options in haas.cfg"""
    return client.Client(session=keystone_session)


@pytest.fixture
def keystone_project_uuids(keystone_client):
    """Return a dictionary mapping openstack project names to UUIDs.

    The keystone setup script randomizes the UUIDs, so we need to query;
    we can't just hardcode.
    """
    return dict([(project.name, project.id)
                 for project in keystone_client.projects.list()])


@pytest.fixture
def server_init():
    server.register_drivers()
    server.validate_state()


@pytest.fixture
def keystone_projects(keystone_project_uuids):
    """Add each of the projects to the HaaS database.

    keystone_project_uuids is the return value from the fixture of the same
    name.
    """
    with app.test_request_context():
        for name in ('admin', 'service'):
            model.db.session.add(model.Project(keystone_project_uuids[name]))
        model.db.session.commit()


@pytest.fixture
def extra_apis(keystone_project_uuids):
    """Register custom api calls for use with the tests.

    Each of these is a no-op, but with different authorization requirements.
    In particular:

        * GET /admin-only requires admin access
        * GET /project-only/<project_name> requires access to `project_name`.
        * GET /anyone requires no special access.
    """

    backend = auth.get_auth_backend()

    @rest.rest_call('GET', '/admin-only', Schema({}))
    def admin_only():
        backend.require_admin()

    @rest.rest_call('GET', '/project-only/<project_name>', Schema({
        'project_name': basestring,
    }))
    def project_only(project_name):
        project_uuid = keystone_project_uuids[project_name]
        project = model.Project.query.filter_by(label=project_uuid).one()
        backend.require_project_access(project)

    @rest.rest_call('GET', '/anyone', Schema({}))
    def anyone():
        pass


@pytest.fixture
def launch_server():
    """Launch the haas API server in another thread.

    The keystone client will try to make *real* http requests, so we can't
    just use flask's built-in test fixtures; we need to actually be listening
    on a port.

    Starts the server listening on port 6000. Will not return until the
    server is actually accepting connections.

    We use 6000 instead of the usual 5000, because the latter is used by
    keystone itself.
    """
    # `debug=False` is required because otherwise something in the
    # implementation of werkzeug calls `signal`, and we get a
    # `ValueError` because (apparently) this doesn't work outside of
    # the main thread.
    Thread(target=lambda: rest.serve(port=6000,
                                     debug=False)).start()

    # Poll the server to see if it's accepting connections yet:
    while True:
        try:
            requests.get('http://localhost:6000')
            return
        except requests.exceptions.ConnectionError:
            time.sleep(0.2)


pytestmark = pytest.mark.usefixtures('configure',
                                     'fresh_database',
                                     'keystone_session',
                                     'keystone_client',
                                     'keystone_project_uuids',
                                     'extra_apis',
                                     'server_init',
                                     'launch_server')


def _do_get(sess, path):
    """Preform an api call on url path `path`, using keystone sesion `sess`.

    `path` is the path portion of the URL to the API call, with no leading
           slash.
    `sess` is a keystone session object.

    returns a response object.

    Unlike keystone's session objects, this returns a response object even
    on failing status codes, rather than raising an exception.
    """
    try:
        return sess.get('http://localhost:6000/' + path)
    except HttpError as e:
        return e.response


@pytest.mark.parametrize('user_info', user_db)
def test_admin_call(keystone_projects, user_info):
    sess = _get_keystone_session(username=user_info['name'],
                                 password=user_info['password'],
                                 project_name=user_info['project_name'])
    resp = _do_get(sess, 'admin-only')
    if user_info['admin']:
        assert resp.status_code < 300, (
            "Status code for admin-only call should be successful for admin."
        )
    else:
        assert 400 < resp.status_code <= 500, (
            "Status code for admin-only call by non-admin should fail!"
        )


@pytest.mark.parametrize('caller_info,project_name', [
    (user, project) for user in user_db for project in project_db
])
def test_project_call(keystone_projects, caller_info, project_name):
    sess = _get_keystone_session(username=caller_info['name'],
                                 password=caller_info['password'],
                                 project_name=caller_info['project_name'])
    resp = _do_get(sess, 'project-only/' + project_name)
    if caller_info['admin'] or caller_info['project_name'] == project_name:
        assert 200 <= resp.status_code < 300, (
            "Status code for project-only call should be successful for "
            "admins and that project."
        )
    else:
        assert 400 < resp.status_code <= 500, (
            "Status code for project-only call by other (non-admin) projects "
            "should fail."
        )


@pytest.mark.parametrize('caller_info', user_db)
def test_anyone_call_authenticated(keystone_projects, caller_info):
    sess = _get_keystone_session(username=caller_info['name'],
                                 password=caller_info['password'],
                                 project_name=caller_info['project_name'])
    resp = _do_get(sess, 'anyone')
    assert 200 <= resp.status_code < 300, (
        "Status code for call with no special authorization requirements "
        "should succeed for any authenticated project in the db!"
    )


def test_anyone_call_unknown_project(keystone_projects):
    # Calls to the API with no special authorization requirements should fail
    # if the user is not authenticated for a project in the database. This is
    # true even if the project exists in keystone; it must be added to the
    # HaaS database before it will be recognized as valid.

    # This user is created in `/ci/keystone/keystone.sh` for use by this test
    # (but naturally is never added to tha haas db).
    sess = _get_keystone_session(username='non-haas-user',
                                 password='secret',
                                 project_name='non-haas-project')
    resp = _do_get(sess, 'anyone')
    assert 400 <= resp.status_code < 500, (
        "Status code for call with no special authorization requirements "
        "should still fail if the keystone project is not in the HaaS db!"
    )


def test_unregistered_admin():
    # Admin-only calls should still work when invoked by anopenstack admin,
    # even when that admin's project does not exist in the database.
    sess = _get_keystone_session(username='admin',
                                 password='s3cr3t',
                                 project_name='admin')
    resp = _do_get(sess, 'admin-only')
    assert 200 <= resp.status_code < 300, (
        "Status code for admin-only call by non-registered admin project "
        "should still succeed."
    )
