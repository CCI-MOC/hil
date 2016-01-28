
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


@pytest.mark.parametrize('fn,error,admin,project,args', [
    # TODO: Find out if there's a way to pass these by kwargs; it would be more
    # readable. For now, we try to make things a little better by formatting
    # each entry as:
    #
    # (fn, error,
    #  admin, project,
    #  args),

    # network_create

    ### Legal cases:

    ### Admin creates a public network internal to HaaS:
    (api.network_create, None,
     True, None,
     ['pub', 'admin', '', '']),

    ### Admin creates a public network with an existing net_id:
    (api.network_create, None,
     True, None,
     ['pub', 'admin', '', 'some-id']),

    ### Admin creates a provider network for some project:
    (api.network_create, None,
     True, None,
     ['pxe', 'admin', 'runway', 'some-id']),

    ### Admin creates an allocated network on behalf of a project. Silly, but
    ### legal.
    (api.network_create, None,
     True, None,
     ['pxe', 'admin', 'runway', '']),

    ### Project creates a private network for themselves:
    (api.network_create, None,
     False, 'runway',
     ['pxe', 'runway', 'runway', '']),

    ## Illegal cases:

    ### Project tries to create a private network for another project.
    (api.network_create, AuthorizationError,
     False, 'runway',
     ['pxe', 'manhattan', 'manhattan', '']),

    ### Project tries to specify a net_id:
    (api.network_create, BadArgumentError,
     False, 'runway',
     ['pxe', 'runway', 'runway', 'some-id']),

    ### Project tries to create a public network:
    (api.network_create, AuthorizationError,
     False, 'runway',
     ['pub', 'admin', '', '']),

    ### Project tries to set creator to 'admin' on its own network:
    (api.network_create, AuthorizationError,
     False, 'runway',
     ['pxe', 'admin', 'runway', '']),
])
def test_auth_call(fn, error, admin, project, args):
    """Test the authorization properties of an api call.

    Parmeters:

        * `fn` - the api function to call
        * `error` - The error that should be raised. None if no error should
                    be raised.
        * `admin` - Whether the request should have admin access.
        * `project` - The name of the project the request should be
                      authenticated as. Can be None if `admin` is True.
        * `args` - the arguments (as a list) to `fn`.
    """
    auth_backend = get_auth_backend()
    auth_backend.set_admin(admin)
    if not admin:
        project = local.db.query(model.Project).filter_by(label=project).one()
        auth_backend.set_project(project)

    if error is None:
        fn(*args)
    else:
        with pytest.raises(error):
            fn(*args)
