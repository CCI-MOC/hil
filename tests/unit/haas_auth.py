"""Test general properties of the authentication framework.

This module is called `haas_auth` because pytest is lousy about namespacing;
if we call it `auth`, it chokes on the fact that there's a file `api/auth.py`
as well. grr.
"""
import pytest
from haas import config, server
from haas.auth import get_auth_backend
from haas.test_common import config_testsuite, config_merge, do_request, \
    fresh_database


@pytest.fixture
def configure():
    config_testsuite()
    config_merge({
        'extensions': {
            'haas.ext.auth.mock': '',

            # This extension is enabled by default in the tests, so we need to
            # disable it explicitly:
            'haas.ext.auth.null': None,

            'haas.ext.switches.mock': '',
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

pytestmark = pytest.mark.usefixtures('configure',
                                     'db',
                                     'server_init')


def test_require_auth():
    """require_authenticate=True should deny calls with "no special access."

    This is the default setting. We use list_free_nodes as an example here.
    """
    auth_backend = get_auth_backend()
    auth_backend.set_auth_success(False)
    resp = do_request('GET', '/free_nodes')
    assert resp.status_code == 401
