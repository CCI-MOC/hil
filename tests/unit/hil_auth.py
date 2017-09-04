"""Test general properties of the authentication framework.

This module is called `hil_auth` because pytest is lousy about namespacing;
if we call it `auth`, it chokes on the fact that there's a file `api/auth.py`
as well. grr.
"""
import pytest
from hil import config
from hil.auth import get_auth_backend
from hil.rest import app
from hil.test_common import config_testsuite, config_merge, fresh_database, \
    fail_on_log_warnings, server_init

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)
server_init = pytest.fixture(server_init)
fresh_database = pytest.fixture(fresh_database)


@pytest.fixture
def configure():
    """Configure HIL"""
    config_testsuite()
    config_merge({
        'extensions': {
            'hil.ext.auth.mock': '',

            # This extension is enabled by default in the tests, so we need to
            # disable it explicitly:
            'hil.ext.auth.null': None,

            'hil.ext.switches.mock': '',
        },
    })
    config.load_extensions()


pytestmark = pytest.mark.usefixtures('configure',
                                     'fresh_database',
                                     'server_init')


def test_require_auth():
    """require_authenticate=True should deny calls with "no special access."

    This is the default setting. We use list_nodes free as an example here.
    """
    auth_backend = get_auth_backend()
    auth_backend.set_auth_success(False)
    client = app.test_client()
    resp = client.get('/node/free')
    assert resp.status_code == 401
