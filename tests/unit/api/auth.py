
import pytest
import unittest
from haas import api, config, model, server, deferred
from haas.network_allocator import get_network_allocator
from haas.rest import RequestContext, local
from haas.auth import get_auth_backend
from haas.errors import AuthorizationError, BadArgumentError, \
    ProjectMismatchError
from haas.test_common import config_testsuite, config_merge, fresh_database


@pytest.fixture
def configure():
    config_testsuite()
    config_merge({
        'extensions': {
            'haas.ext.auth.mock': '',

            # This extension is enabled by default in the tests, so we need to
            # disable it explicitly:
            'haas.ext.auth.null': None,
        },
    })
    config.load_extensions()


@pytest.fixture
def db(request):
    session = fresh_database(request)
    # Create a couple projects:
    runway = model.Project("runway")
    manhattan = model.Project("manhattan")
    for proj in [runway, manhattan]:
        session.add(proj)

    # ...A variety of networks:

    networks = [
        {
            'creator': None,
            'access': None,
            'allocated': True,
            'label': 'stock_int_pub',
        },
        {
            'creator': None,
            'access': None,
            'allocated': False,
            'network_id': 'ext_pub_chan',
            'label': 'stock_ext_pub',
        },
        {
            'creator': runway,
            'access': runway,
            'allocated': True,
            'label': 'runway_pxe'
        },
        {
            'creator': None,
            'access': runway,
            'allocated': False,
            'network_id': 'runway_provider_chan',
            'label': 'runway_provider',
        },
        {
            'creator': manhattan,
            'access': manhattan,
            'allocated': True,
            'label': 'manhattan_pxe'
        },
        {
            'creator': None,
            'access': manhattan,
            'allocated': False,
            'network_id': 'manhattan_provider_chan',
            'label': 'manhattan_provider',
        },
    ]

    for net in networks:
        if net['allocated']:
            net['network_id'] = \
                get_network_allocator().get_new_network_id(session)
        session.add(model.Network(**net))

    # ... Some nodes (with projets):
    nodes = [
        {'label': 'runway_node_0', 'project': runway},
        {'label': 'runway_node_1', 'project': runway},
        {'label': 'manhattan_node_0', 'project': manhattan},
        {'label': 'manhattan_node_1', 'project': manhattan},
        {'label': 'free_node_0', 'project': None},
        {'label': 'free_node_1', 'project': None},
    ]
    for node_dict in nodes:
        node = model.Node(node_dict['label'], '', '', '')
        node.project = node_dict['project']
        session.add(model.Nic(node, label='boot-nic', mac_addr='Unknown'))

    # at least one node with no nics (useful for testing delete):
    session.add(model.Node('no_nic_node', '', '', ''))
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

    ### Project tries to specify a net_id. This raises a different exception
    ### than the rest for historical reasons, which is fine, but we should
    ### still make sure it raises *something*.
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

    # network_delete

    ## Legal cases

    ### admin should be able to delete any network:
] +
    [
        (api.network_delete, None,
         True, None,
         [net]) for net in [
            'stock_int_pub',
            'stock_ext_pub',
            'runway_pxe',
            'runway_provider',
            'manhattan_pxe',
            'manhattan_provider',
            ]
    ] + [
    ### project should be able to delete it's own (created) network:
    (api.network_delete, None,
     False, 'runway',
     ['runway_pxe']),

    ## Illegal cases:

] +
    ### Project should not be able to delete admin-created networks.
    [(api.network_delete, AuthorizationError,
      False, 'runway',
      [net]) for net in [
          'stock_int_pub',
          'stock_ext_pub',
          'runway_provider',  # ... including networks created for said project.
          ]
    ] +
    ### Project should not be able to delete networks created by other projects.
    [(api.network_delete, AuthorizationError,
      False, 'runway',
      [net]) for net in [
          'manhattan_pxe',
          'manhattan_provider',
          ]
    ] +

    # show_network

    ## Legal cases

    ### Public networks should be accessible by anyone:
    [(api.show_network, None,
      admin, project,
      [net]) for net in [
          'stock_int_pub',
          'stock_ext_pub',
      ] for project in [
          'runway',
          'manhattan',
      ] for admin in (True, False)] +

    ### Projects should be able to view networks they have access to:
    [(api.show_network, None,
      False, project,
      [net]) for (project, net) in [
          ('runway', 'runway_pxe'),
          ('runway', 'runway_provider'),
          ('manhattan', 'manhattan_pxe'),
          ('manhattan', 'manhattan_provider'),
      ]] +

    ## Illegal cases

    ### Projects should not be able to access each other's networks:
    [(api.show_network, AuthorizationError,
      False, project,
      [net]) for (project, net) in [
          ('runway', 'manhattan_pxe'),
          ('runway', 'manhattan_provider'),
          ('manhattan', 'runway_pxe'),
          ('manhattan', 'runway_provider'),
      ]] +

    # node_connect_network

    ## Legal cases

    ### Projects should be able to connect their own nodes to their own networks.
    [(api.node_connect_network, None,
      False, project,
      [node, 'boot-nic', net]) for (project, node, net) in [
          ('runway', 'runway_node_0', 'runway_pxe'),
          ('runway', 'runway_node_1', 'runway_provider'),
          ('manhattan', 'manhattan_node_0', 'manhattan_pxe'),
          ('manhattan', 'manhattan_node_1', 'manhattan_provider'),
      ]] +

    ### Projects should be able to connect their nodes to public networks.
    [(api.node_connect_network, None,
      False, project,
      [node, 'boot-nic', net]) for (project, node) in [
          ('runway', 'runway_node_0'),
          ('runway', 'runway_node_1'),
          ('manhattan', 'manhattan_node_0'),
          ('manhattan', 'manhattan_node_1'),
      ] for net in ('stock_int_pub', 'stock_ext_pub')] +

     ## Illegal cases

     ### Projects should not be able to connect their nodes to each other's
     ### networks. Note that this raises a different exception than the other
     ### auth related failures. The reasons are historical, but the main thing
     ### is that it should raise *something*.
     [(api.node_connect_network, ProjectMismatchError,
       False, 'runway',
       [node, 'boot-nic', net]) for (node, net) in [
           ('runway_node_0', 'manhattan_pxe'),
           ('runway_node_1', 'manhattan_provider'),
       ]] +

[
    ### Projects should not be able to attach each other's nodes to public networks.
    (api.node_connect_network, AuthorizationError,
       False, 'runway',
       ['manhattan_node_0', 'boot-nic', 'stock_int_pub']),

    ### Projects should not be able to attach free nodes to networks.
    ### The same node about the exception as above applies.
    (api.node_connect_network, ProjectMismatchError,
     False, 'runway',
     ['free_node_0', 'boot-nic', 'stock_int_pub']),
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


# There are a whole bunch of api calls that just unconditionally require admin
# access. This is  a list of (function, args) pairs, each of which should
# succed as admin and fail as a regular project. The actual test functions for
# these are below.
admin_calls = [
    (api.node_register, ['new_node', '', '', '']),
    (api.node_delete, ['no_nic_node']),
]


@pytest.mark.parametrize('fn,args', admin_calls)
def test_admin_succeed(fn, args):
    auth_backend = get_auth_backend()
    auth_backend.set_admin(True)
    auth_backend.set_project(None)
    fn(*args)


@pytest.mark.parametrize('fn,args', admin_calls)
def test_admin_fail(fn, args):
    auth_backend = get_auth_backend()
    auth_backend.set_admin(False)
    runway = local.db.query(model.Project).filter_by(label='runway').one()
    auth_backend.set_project(runway)
    with pytest.raises(AuthorizationError):
        fn(*args)


class Test_node_detach_network(unittest.TestCase):

    def setUp(self):
        self.auth_backend = get_auth_backend()
        self.runway = local.db.query(model.Project).filter_by(label='runway').one()
        self.manhattan = local.db.query(model.Project).filter_by(label='manhattan').one()
        self.auth_backend.set_project(self.manhattan)
        api.node_connect_network('manhattan_node_0', 'boot-nic', 'stock_int_pub')
        deferred.apply_networking()

    def test_success(self):
        self.auth_backend.set_project(self.manhattan)
        api.node_detach_network('manhattan_node_0', 'boot-nic', 'stock_int_pub')

    def test_wrong_project(self):
        self.auth_backend.set_project(self.runway)
        with pytest.raises(AuthorizationError):
            api.node_detach_network('manhattan_node_0', 'boot-nic', 'stock_int_pub')
