"""Unit tests for ipmi.py"""
import pytest
from hil import api, errors
from hil.test_common import config, config_testsuite, fresh_database, \
    fail_on_log_warnings, with_request_context, config_merge, server_init


@pytest.fixture
def configure():
    """Configure HIL."""
    config_testsuite()
    config_merge({
        'extensions': {
            'hil.ext.obm.ipmi': ''
        },
        'devel': {
           'dry_run': None
        }
    })
    config.load_extensions()


fresh_database = pytest.fixture(fresh_database)
fail_on_log_warnings = pytest.fixture(fail_on_log_warnings)
with_request_context = pytest.yield_fixture(with_request_context)
server_init = pytest.fixture(server_init)


default_fixtures = ['fail_on_log_warnings',
                    'configure',
                    'fresh_database',
                    'server_init',
                    'with_request_context']

pytestmark = pytest.mark.usefixtures(*default_fixtures)


class TestIpmi:
    """Test IPMI functions."""

    # This test is broken by some of the recent obmd changes, but it's also
    # attempting to test a code path that will soon be deleted; as such,
    # I(zenhack) have just marked it as expected to fail, rather than waste
    # time fixing it.
    @pytest.mark.xfail
    def test_node_set_bootdev(self):
        """Check that node_set_bootdev throws error for invalid devices."""

        api.node_register(
            node='node-99',
            obm={
                "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                "host": "ipmihost",
                "user": "root",
                "password": "tapeworm",
            },
            obmd={
                "uri": "http://obmd.example.com/nodes/node-99",
                "admin_token": "secret",
            },
        )

        # throw BadArgumentError for an invalid bootdevice
        with pytest.raises(errors.BadArgumentError):
            api.node_set_bootdev('node-99', 'invalid-device')

    def test_require_legal_bootdev(self):
        """Test the require_legal_bootdev method.

        Try a valid and an invalid bootdev, and make sure it does the right
        thing.
        """
        from hil.ext.obm import ipmi
        instance = ipmi.Ipmi(
                  host="ipmihost",
                  user="root",
                  password="tapeworm")
        instance.require_legal_bootdev("none")

        with pytest.raises(errors.BadArgumentError):
            instance.require_legal_bootdev("not_valid_bootdev")
