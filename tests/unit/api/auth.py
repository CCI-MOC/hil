"""Tests related to the authorization of api calls.

NOTE: while all of these are conceptually authorization related, some illegal
operations will raise exceptions other than AuthorizationError. This usually
happens when the operation is illegal *in principle*, and would not be fixed by
authenticating as someone else. We were already raising exceptions in
these cases before actually adding authentication and authorization to
the mix. They are still tested here, since they are important for security.
"""

import pytest
import unittest
from hil import api, config, model, deferred
from hil.auth import get_auth_backend
from hil.errors import AuthorizationError, BadArgumentError, \
    ProjectMismatchError, BlockedError
from hil.test_common import config_testsuite, config_merge, fresh_database, \
    with_request_context, additional_db, fail_on_log_warnings, server_init

MOCK_OBM_API_NAME = 'http://schema.massopencloud.org/haas/v0/obm/mock'
MOCK_SWITCH_API_NAME = 'http://schema.massopencloud.org/haas/v0/switches/mock'


def auth_call_test(fn, error, admin, project, args, kwargs={}):
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
        project = model.Project.query \
            .filter_by(label=project).one()
        auth_backend.set_project(project)

    if error is None:
        fn(*args, **kwargs)
    else:
        with pytest.raises(error):
            fn(*args, **kwargs)


additional_db = pytest.fixture(additional_db)
fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


@pytest.fixture
def configure():
    "Configure HIL"
    config_testsuite()
    config_merge({
        'extensions': {
            'hil.ext.auth.mock': '',

            # This extension is enabled by default in the tests, so we need to
            # disable it explicitly:
            'hil.ext.auth.null': None,
            'hil.ext.switches.mock': '',
            'hil.ext.obm.mock': ''
        },
    })
    config.load_extensions()


fresh_database = pytest.fixture(fresh_database)
with_request_context = pytest.yield_fixture(with_request_context)
server_init = pytest.fixture(server_init)


pytestmark = pytest.mark.usefixtures('configure',
                                     'fresh_database',
                                     'additional_db',
                                     'server_init',
                                     'with_request_context')


# We have a *lot* of different parameters with which we're going to invoke
# `test_auth_call`, below. Rather than passing one giant list to the decorator
# in-line, we construct it in stages here:


auth_call_params = [
    #
    # network_create
    #

    # Legal Cases:
    # Admin creates a public network internal to HIL.
    dict(fn=api.network_create,
         error=None,
         admin=True,
         project=None,
         args=['pub', 'admin', '', '']),

    # Admin creates a public network with an existing net_id.
    dict(fn=api.network_create,
         error=None,
         admin=True,
         project=None,
         args=['pub', 'admin', '', 'some-id']),

    # Admin creates a provider network for some project.
    dict(fn=api.network_create,
         error=None,
         admin=True,
         project=None,
         args=['pxe', 'admin', 'runway', 'some-id']),

    # Admin creates an allocated network on behalf of a project.
    dict(fn=api.network_create,
         error=None,
         admin=True,
         project=None,
         args=['pxe', 'admin', 'runway', '']),

    # Project creates a private network for themselves.
    dict(fn=api.network_create,
         error=None,
         admin=False,
         project='runway',
         args=['pxe', 'runway', 'runway', '']),

    # Illegal Cases:
    # Project tries to create a private network for another project.
    dict(fn=api.network_create,
         error=AuthorizationError,
         admin=False,
         project='runway',
         args=['pxe', 'manhattan', 'manhattan', '']),

    # Project tries to specify a net_id.
    dict(fn=api.network_create,
         error=BadArgumentError,
         admin=False,
         project='runway',
         args=['pxe', 'runway', 'runway', 'some-id']),

    # Project tries to create a public network.
    dict(fn=api.network_create,
         error=AuthorizationError,
         admin=False,
         project='runway',
         args=['pub', 'admin', '', '']),

    # Project tries to set owner to 'admin' on its own network:
    dict(fn=api.network_create,
         error=AuthorizationError,
         admin=False,
         project='runway',
         args=['pxe', 'admin', 'runway', '']),
]

#
# network_delete
#

# Legal Cases
# Admin should be able to delete any network.
for net in [
    'stock_int_pub',
    'stock_ext_pub',
    'runway_pxe',
    'runway_provider',
    'manhattan_pxe',
    'manhattan_provider',
]:
    auth_call_params.append(dict(
        fn=api.network_delete,
        error=None,
        admin=True,
        project=None,
        args=[net]
    ))

# Project should be able to delete it's own (created) network.
auth_call_params.append(dict(
    fn=api.network_delete,
    error=None,
    admin=False,
    project='runway',
    args=['runway_pxe']
))

# Illegal Cases:
# Project should not be able to delete admin-created networks.
for net in [
    'stock_int_pub',
    'stock_ext_pub',
    'runway_provider',  # ... including networks created for said project.
    'manhattan_runway_provider',
]:
    auth_call_params.append(dict(
        fn=api.network_delete,
        error=AuthorizationError,
        admin=False,
        project='runway',
        args=[net]
    ))

# Project should not be able to delete networks created by other projects.
for net in [
    'manhattan_pxe',
    'manhattan_provider',
    'manhattan_runway_pxe',
]:
    auth_call_params.append(dict(
        fn=api.network_delete,
        error=AuthorizationError,
        admin=False,
        project='runway',
        args=[net]))

#
# network_grant_project_access
#

# Legal cases
# admin should be able to add  access to a network
# for any project (that does not already have access)
for (project, net) in [
    ('manhattan', 'runway_provider'),
    ('runway', 'manhattan_provider'),
    ('runway', 'manhattan_pxe'),
    ('manhattan', 'runway_pxe'),
]:
    auth_call_params.append(dict(
        fn=api.network_grant_project_access,
        error=None,
        admin=True,
        project=None,
        args=[project, net]
    ))

# project that is the owner of the network should
# be able to add access for other projects
for (project, project_access, net) in [
    ('manhattan', 'runway', 'manhattan_pxe'),
    ('runway', 'manhattan', 'runway_pxe'),
]:
    auth_call_params.append(dict(
        fn=api.network_grant_project_access,
        error=None,
        admin=False,
        project=project,
        args=[project_access, net]
    ))


# Illegal cases:
# Projects other than the network owner should not be ble to grant access
for (project, project_access, net) in [
    ('manhattan', 'manhattan', 'runway_pxe'),
    ('runway', 'runway', 'manhattan_pxe'),
]:
    auth_call_params.append(dict(
        fn=api.network_grant_project_access,
        error=AuthorizationError,
        admin=False,
        project=project,
        args=[project_access, net]
    ))

#
# network_revoke_project_access
#

# Legal cases
# admin should be able to remove access to a network
# for any project (that was not the owner of the network)
# admin created networks with all the access removed will become
# public networks
for (project, net) in [
    ('runway', 'runway_provider'),
    ('runway', 'manhattan_runway_pxe'),
    ('manhattan', 'manhattan_provider'),
    ('runway', 'manhattan_runway_provider'),
    ('manhattan', 'manhattan_runway_provider'),
]:
    auth_call_params.append(dict(
        fn=api.network_revoke_project_access,
        error=None,
        admin=True,
        project=None,
        args=[project, net]
    ))

# project that is the owner of the network should
# be able to remove the access of other projects
# projects should be able to remove their own access
for (project, project_access, net) in [
    ('manhattan', 'runway', 'manhattan_runway_pxe'),
    ('runway', 'runway', 'manhattan_runway_pxe'),
    ('manhattan', 'manhattan', 'manhattan_runway_provider'),
    ('runway', 'runway', 'manhattan_runway_provider'),
]:
    auth_call_params.append(dict(
        fn=api.network_revoke_project_access,
        error=None,
        admin=False,
        project=project,
        args=[project_access, net]
    ))


# Illegal cases:
# Projects other than the network owner or the project
# itself should  not be able to remove access of other projects
for (project, project_access, net) in [
    ('manhattan', 'runway', 'manhattan_runway_provider'),
]:
    auth_call_params.append(dict(
        fn=api.network_revoke_project_access,
        error=AuthorizationError,
        admin=False,
        project=project,
        args=[project_access, net]
    ))

#
# list_network_attachments
#

# Legal cases
# Admin should be able to list attachments for public network:
for net in ('stock_int_pub', 'stock_ext_pub'):
    for project in ('runway', 'manhattan'):
            auth_call_params.append(dict(
                fn=api.list_network_attachments,
                error=None,
                admin=True,
                project=project,
                args=[net]
            ))

# Projects should be able to view their own nodes in a network:
for (project, net) in [
    ('runway', 'runway_pxe'),
    ('runway', 'runway_provider'),
    ('manhattan', 'manhattan_pxe'),
    ('manhattan', 'manhattan_provider'),
    ('manhattan', 'manhattan_runway_pxe'),
    ('manhattan', 'manhattan_runway_provider'),
    ('runway', 'manhattan_runway_pxe'),
    ('runway', 'manhattan_runway_provider'),
]:
    auth_call_params.append(dict(
        fn=api.list_network_attachments,
        error=None,
        admin=False,
        project=project,
        args=[net, project]
    ))

# owner of a network should be able to view all nodes in the network:
for (project, net) in [
    ('runway', 'runway_pxe'),
    ('manhattan', 'manhattan_pxe'),
    ('manhattan', 'manhattan_runway_pxe'),
]:
    auth_call_params.append(dict(
        fn=api.list_network_attachments,
        error=None,
        admin=False,
        project=project,
        args=[net]
    ))


# Illegal cases
# Projects should not be able to list nodes that do not belong to them
# (on network they do not own)
for (project, access_project, net) in [
    ('runway', 'manhattan', 'manhattan_runway_pxe'),
    ('runway', 'manhattan', 'manhattan_runway_provider'),
    ('runway', None, 'manhattan_runway_pxe'),
    ('runway', None, 'manhattan_runway_provider'),
]:
    auth_call_params.append(dict(
        fn=api.list_network_attachments,
        error=AuthorizationError,
        admin=False,
        project=project,
        args=[net, access_project]
    ))

# or on networks they do not have access to
for (project, net) in [
    ('runway', 'manhattan_pxe'),
    ('runway', 'manhattan_provider'),
    ('manhattan', 'runway_pxe'),
    ('manhattan', 'runway_provider'),
]:
    auth_call_params.append(dict(
        fn=api.list_network_attachments,
        error=AuthorizationError,
        admin=False,
        project=project,
        args=[net, project]
    ))

#
# show_network
#

# Legal Cases
# Public networks should be accessible by anyone.
for net in ('stock_int_pub', 'stock_ext_pub'):
    for project in ('runway', 'manhattan'):
        for admin in (True, False):
            auth_call_params.append(dict(
                fn=api.show_network,
                error=None,
                admin=admin,
                project=project,
                args=[net]
            ))

# Projects should be able to view networks they have access to.
for (project, net) in [
    ('runway', 'runway_pxe'),
    ('runway', 'runway_provider'),
    ('manhattan', 'manhattan_pxe'),
    ('manhattan', 'manhattan_provider'),
    ('manhattan', 'manhattan_runway_pxe'),
    ('manhattan', 'manhattan_runway_provider'),
    ('runway', 'manhattan_runway_pxe'),
    ('runway', 'manhattan_runway_provider'),
]:
    auth_call_params.append(dict(
        fn=api.show_network,
        error=None,
        admin=False,
        project=project,
        args=[net]
    ))

# Illegal Cases
# Projects should not be able to access each other's networks.
for (project, net) in [
    ('runway', 'manhattan_pxe'),
    ('runway', 'manhattan_provider'),
    ('manhattan', 'runway_pxe'),
    ('manhattan', 'runway_provider'),
]:
    auth_call_params.append(dict(
        fn=api.show_network,
        error=AuthorizationError,
        admin=False,
        project=project,
        args=[net]
    ))

#
# node_connect_network
#

# Legal Cases
# Projects should be able to connect their own nodes to their own networks.
for (project, node, net) in [
    ('runway', 'runway_node_0', 'runway_pxe'),
    ('runway', 'runway_node_1', 'runway_provider'),
    ('manhattan', 'manhattan_node_0', 'manhattan_pxe'),
    ('manhattan', 'manhattan_node_1', 'manhattan_provider'),
]:
    auth_call_params.append(dict(
        fn=api.node_connect_network,
        error=None,
        admin=False,
        project=project,
        args=[node, 'boot-nic', net]
    ))


# Projects should be able to connect their nodes to public networks.
for net in ('stock_int_pub', 'stock_ext_pub'):
    for (project, node) in [
          ('runway', 'runway_node_0'),
          ('runway', 'runway_node_1'),
          ('manhattan', 'manhattan_node_0'),
          ('manhattan', 'manhattan_node_1'),
    ]:
        auth_call_params.append(dict(
            fn=api.node_connect_network,
            error=None,
            admin=False,
            project=project,
            args=[node, 'boot-nic', net]))

# Illegal Cases
# Projects are not able to connect their nodes to each other's networks.
for (node, net) in [
    ('runway_node_0', 'manhattan_pxe'),
    ('runway_node_1', 'manhattan_provider'),
]:
    auth_call_params.append(dict(
         fn=api.node_connect_network,
         error=ProjectMismatchError,
         admin=False,
         project='runway',
         args=[node, 'boot-nic', net]
     ))

auth_call_params += [
    # Projects are not able to attach each other's nodes to public networks.
    dict(fn=api.node_connect_network,
         error=AuthorizationError,
         admin=False,
         project='runway',
         args=['manhattan_node_0', 'boot-nic', 'stock_int_pub']),

    # Projects should not be able to attach free nodes to networks.
    # The same node about the exception as above applies.
    dict(fn=api.node_connect_network,
         error=ProjectMismatchError,
         admin=False,
         project='runway',
         args=['free_node_0', 'boot-nic', 'stock_int_pub']),

    #
    # list_project_nodes
    #

    # Legal Cases
    # Admin lists a project's nodes.
    dict(fn=api.list_project_nodes,
         error=None,
         admin=True,
         project=None,
         args=['runway']),

    # Project lists its own nodes.
    dict(fn=api.list_project_nodes,
         error=None,
         admin=False,
         project='runway',
         args=['runway']),

    # Illegal Cases
    # Project lists another project's nodes.
    dict(fn=api.list_project_nodes,
         error=AuthorizationError,
         admin=False,
         project='runway',
         args=['manhattan']),

    #
    # show_node
    #

    # Legal Cases:
    # Project shows a free node.
    dict(fn=api.show_node,
         error=None,
         admin=False,
         project='runway',
         args=['free_node_0']),

    # Project shows its own node.
    dict(fn=api.show_node,
         error=None,
         admin=False,
         project='runway',
         args=['runway_node_0']),

    # Illegal Cases:
    # Project tries to show another project's node.
    dict(fn=api.show_node,
         error=AuthorizationError,
         admin=False,
         project='runway',
         args=['manhattan_node_0']),

    #
    # project_connect_node:
    #

    # Project tries to connect someone else's node to itself. The basic cases
    # of connecting a free node are covered by project_calls, below.
    dict(fn=api.project_connect_node,
         error=BlockedError,
         admin=False,
         project='runway',
         args=['runway', 'manhattan_node_0']),
]


@pytest.mark.parametrize('kwargs', auth_call_params)
def test_auth_call(kwargs):
    """Call auth_call_test on our huge list of cases.

    We use auth_call_test in a few other places, hence the separate wrapper
    for the actual test case.
    """
    return auth_call_test(**kwargs)


# There are a whole bunch of api calls that just unconditionally require admin
# access. This is  a list of (function, args) pairs, each of which should
# succed as admin and fail as a regular project. The actual test functions for
# these are below.

admin_calls = [
    (api.node_register, ['new_node'], {'obm': {
              "type": MOCK_OBM_API_NAME,
              "host": "ipmihost",
              "user": "root",
              "password": "tapeworm"}}),
    # (api.node_register, ['new_node', obm=obm, {}),
    (api.node_delete, ['no_nic_node'], {}),
    (api.node_register_nic, ['free_node_0', 'extra-nic',
                             'de:ad:be:ef:20:16'], {}),
    (api.node_delete_nic, ['free_node_0', 'boot-nic'], {}),
    (api.project_create, ['anvil-nextgen'], {}),
    (api.list_projects, [], {}),

    # node_power_* and node_set_bootdev, on free nodes only.
    # Nodes assigned to a project are tested in project_calls, below.
    (api.node_power_cycle, ['free_node_0'], {}),
    (api.node_power_off, ['free_node_0'], {}),
    (api.node_set_bootdev, ['free_node_0'], {'bootdev': {'none'}}),

    (api.project_delete, ['empty-project'], {}),

    (api.switch_register, ['new-switch', MOCK_SWITCH_API_NAME], {
        'hostname': 'oak-ridge',
        'username': 'alice',
        'password': 'changeme',
    }),
    (api.switch_delete, ['empty-switch'], {}),
    (api.switch_register_port, ['stock_switch_0', 'gi1/0/13'], {}),
    (api.switch_delete_port, ['stock_switch_0', 'free_port_0'], {}),
    (api.port_connect_nic, ['stock_switch_0', 'free_port_0',
                            'free_node_0', 'boot-nic'], {}),
    (api.show_port, ['stock_switch_0', 'free_port_0'], {}),
    (api.port_detach_nic, ['stock_switch_0', 'free_node_0_port'], {}),
    (api.node_set_metadata, ['free_node_0', 'EK', 'pk'], {}),
    (api.node_delete_metadata, ['runway_node_0', 'EK'], {}),
    (api.port_revert, ['stock_switch_0', 'free_node_0_port'], {}),
    (api.list_active_extensions, [], {}),
]


# Similarly, there are a large number of calls that require access to a
# particular project. This is a list of (function, args) pairs that should
# succeed as project 'runway', and fail as project 'manhattan'.
project_calls = [
    # node_power_* and node_set_bootdev, on allocated nodes only.
    # Free nodes are testsed in admin_calls, above.
    (api.node_power_cycle, ['runway_node_0'], {}),
    (api.node_power_off, ['runway_node_0'], {}),
    (api.node_set_bootdev, ['runway_node_0'], {'bootdev': {'none'}}),

    (api.project_connect_node, ['runway', 'free_node_0'], {}),
    (api.project_detach_node, ['runway', 'runway_node_0'], {}),

    (api.headnode_create, ['new-headnode', 'runway', 'base-headnode'], {}),
    (api.headnode_delete, ['runway_headnode_off'], {}),
    (api.headnode_start, ['runway_headnode_off'], {}),
    (api.headnode_stop, ['runway_headnode_on'], {}),
    (api.headnode_create_hnic, ['runway_headnode_off', 'extra-hnic'], {}),
    (api.headnode_delete_hnic, ['runway_headnode_off', 'pxe'], {}),

    (api.headnode_connect_network, ['runway_headnode_off',
                                    'pxe', 'stock_int_pub'], {}),
    (api.headnode_connect_network, ['runway_headnode_off',
                                    'pxe', 'runway_pxe'], {}),
    (api.headnode_detach_network, ['runway_headnode_off', 'public'], {}),

    (api.list_project_headnodes, ['runway'], {}),
    (api.show_headnode, ['runway_headnode_on'], {}),
]


@pytest.mark.parametrize('fn,args,kwargs', admin_calls)
def test_admin_succeed(fn, args, kwargs):
    """Verify that a call succeeds as admin."""
    auth_call_test(fn=fn,
                   error=None,
                   admin=True,
                   project=None,
                   args=args,
                   kwargs=kwargs)


@pytest.mark.parametrize('fn,args,kwargs', admin_calls)
def test_admin_fail(fn, args, kwargs):
    """Verify that a call fails when not admin."""
    auth_call_test(fn=fn,
                   error=AuthorizationError,
                   admin=False,
                   project='runway',
                   args=args,
                   kwargs=kwargs)


@pytest.mark.parametrize('fn,args,kwargs', project_calls)
def test_runway_succeed(fn, args, kwargs):
    """Verify that a call succeeds when run as the 'runway' project."""
    auth_call_test(fn=fn,
                   error=None,
                   admin=False,
                   project='runway',
                   args=args,
                   kwargs=kwargs)


@pytest.mark.parametrize('fn,args,kwargs', project_calls)
def test_manhattan_fail(fn, args, kwargs):
    """Verify that a call fails when run as the 'manhattan' project."""
    auth_call_test(fn=fn,
                   error=AuthorizationError,
                   admin=False,
                   project='manhattan',
                   args=args,
                   kwargs=kwargs)


class Test_node_detach_network(unittest.TestCase):
    """Test authorization properties of node_detach_network."""

    def setUp(self):
        """Common setup for the tests.

        * node 'manhattan_node_0' is attached to network 'stock_int_pub', via
          'boot-nic'.

        This also sets some properties for easy access to the projects.
        """
        self.auth_backend = get_auth_backend()
        self.runway = model.Project.query.filter_by(label='runway').one()
        self.manhattan = model.Project.query.filter_by(label='manhattan').one()

        # The individual tests set the right project, but we need this to
        # connect the network during setup:
        self.auth_backend.set_project(self.manhattan)

        api.node_connect_network('manhattan_node_0',
                                 'boot-nic',
                                 'stock_int_pub')
        deferred.apply_networking()

    def test_success(self):
        """Project 'manhattan' can detach its own node."""
        self.auth_backend.set_project(self.manhattan)
        api.node_detach_network('manhattan_node_0',
                                'boot-nic',
                                'stock_int_pub')

    def test_wrong_project(self):
        """Project 'runway' cannot detach "manhattan"'s node."""
        self.auth_backend.set_project(self.runway)
        with pytest.raises(AuthorizationError):
            api.node_detach_network('manhattan_node_0',
                                    'boot-nic',
                                    'stock_int_pub')
