"""Unit tests for the client library.

TODO: we have plans to move ./client.py to integration/, since those
are really integration tests. Once that's done we should move this to
./client.py; it's here now to avoid name collisions/conflicts.
"""

import flask
import pytest
from schema import Schema

from hil import config, rest
from hil.client.base import FailedAPICallException
from hil.client.client import Client
from hil.test_common import HybridHTTPClient, fail_on_log_warnings, \
    server_init, config_testsuite

fail_on_log_warnings = pytest.fixture(fail_on_log_warnings)
server_init = pytest.fixture(server_init)


@pytest.fixture()
def configure():
    """Fixture to load the HIL config."""
    config_testsuite()
    config.load_extensions()


pytestmark = pytest.mark.usefixtures('fail_on_log_warnings',
                                     'configure',
                                     'server_init')


def test_non_json_response():
    """The client library should raise an error when the response body is
    unexpectedly not JSON.
    """
    # Endpoint is arbitrary:
    endpoint = 'http:/127.0.0.1:9933'
    client = Client(endpoint, HybridHTTPClient(endpoint))

    # Override one of the API calls with a different implementation:
    # pylint: disable=unused-variable
    @rest.rest_call('GET', '/nodes/free', Schema({}))
    def list_free_nodes():
        """Mock API call for testing; always raises an error."""
        flask.abort(500)

    try:
        client.node.list('free')
        assert False, 'Client library did not report an error!'
    except FailedAPICallException as e:
        # Make sure it's the right error:
        assert e.error_type == 'unknown', 'Wrong error type.'
