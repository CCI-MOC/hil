
import pytest
from haas import api, config, model, server
from haas.rest import RequestContext, local
from haas.auth import get_auth_backend
from haas.errors import AuthorizationError
from haas.test_common import config_testsuite, config_merge, fresh_database

@pytest.fixture
def configure():
    config_testsuite()
    config_merge({
        'extensions': {
            'haas.ext.auth.mock': '',
            'haas.ext.auth.null': None,
        },
    })
    config.load_extensions()


@pytest.fixture
def db(request):
    session = fresh_database(request)
    session.add(model.Project("runway"))
    session.add(model.Project("manhattan"))
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


pytestmark = pytest.mark.usefixtures('configure',
                                     'db',
                                     'server_init',
                                     'with_request_context')


@pytest.mark.parametrize('ok,admin,project,creator,access,net_id', [
    # TODO: Find out if there's a way to pass these by kwargs; it would be more
    # readable. For now, we try to make things a little better by putting all
    # of the actual arguments to network_create on the second line of each
    # entry.
    (True, False, 'runway',
     'runway', 'runway', ''),
])
def test_network_create(ok, admin, project, creator, access, net_id):
    """Test network_create with various arguments/authentication.

    Parmeters:

        * `auth_backend` - the auth backend. provided by the fixture.
        * `ok` - True ifauthorization should succeed, False otherwise.
        * `admin` - Whether the request should have admin access.
        * `project` - The project the request should be authenticated as.
        * `creator`, `access`, and `net_id` - The arguments to network_create.
    """
    auth_backend = get_auth_backend()
    project = local.db.query(model.Project).filter_by(label=project).one()
    auth_backend.set_admin(admin)
    auth_backend.set_project(project)

    def call():
        api.network_create('pxe', creator, access, net_id)

    if ok:
        call()
    else:
        with pytest.raises(AuthorizationError):
            call()
