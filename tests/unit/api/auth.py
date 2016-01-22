
import pytest
from haas import api, config, model, server
from haas.rest import RequestContext, local
from haas.auth import get_auth_backend
from haas.errors import AuthorizationError, BadArgumentError
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


@pytest.mark.parametrize('error,admin,project,creator,access,net_id', [
    # TODO: Find out if there's a way to pass these by kwargs; it would be more
    # readable. For now, we try to make things a little better by putting all
    # of the actual arguments to network_create on the second line of each
    # entry.

    # Legal cases:

    ## Admin creates a public network internal to HaaS:
    (None, True, None,
     'admin', '', ''),

    ## Admin creates a public network with an existing net_id:
    (None, True, None,
     'admin', '', 'some-id'),

    ## Admin creates a provider network for some project:
    (None, True, None,
     'admin', 'runway', 'some-id'),

    ## Admin creates an allocated network on behalf of a project. Silly, but
    ## legal.
    (None, True, None,
     'admin', 'runway', ''),

    ## Project creates a private network for themselves:
    (None, False, 'runway',
     'runway', 'runway', ''),

    # Illegal cases:

    ## Project tries to create a private network for another project:
    (AuthorizationError, False, 'runway',
     'manhattan', 'manhattan', ''),

    ## Project tries to specify a net_id:
    (BadArgumentError, False, 'runway',
     'runway', 'runway', 'some-id'),

    ## Project tries to create a public network:
    (AuthorizationError, False, 'runway',
     'admin', '', ''),

    ## Project tries to set creator to 'admin' on its own network:
    (AuthorizationError, False, 'runway',
     'admin', 'runway', ''),
])
def test_network_create(error, admin, project, creator, access, net_id):
    """Test network_create with various arguments/authentication.

    Parmeters:

        * `auth_backend` - the auth backend. provided by the fixture.
        * `error` - The error that should be raised. None if no error should
                    be raised.
        * `admin` - Whether the request should have admin access.
        * `project` - The project the request should be authenticated as. Can
                      be None if `admin` is True.
        * `creator`, `access`, and `net_id` - The arguments to network_create.
    """
    auth_backend = get_auth_backend()
    auth_backend.set_admin(admin)
    if not admin:
        project = local.db.query(model.Project).filter_by(label=project).one()
        auth_backend.set_project(project)

    def call():
        api.network_create('pxe', creator, access, net_id)

    if error is None:
        call()
    else:
        with pytest.raises(error):
            call()
