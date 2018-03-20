"""Test the hil.config module."""
from hil.test_common import config_set, fail_on_log_warnings, \
        config_testsuite, config_merge
from hil import config
import sys
import pytest


fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


def test_load_extension():
    """Check that putting modules in [extensions] results in importing them."""
    config_set({
        'extensions': {
            # These modules are chosen because:
            #
            # 1. They are in the standard library, and cross-platform
            # 2. If you ever think you need to import these for use in
            #    HIL, I will judge you.
            'sndhdr': '',
            'colorsys': '',
            'email.mime.audio': '',
        },
    })
    config.load_extensions()
    for module in 'sndhdr', 'colorsys', 'email.mime.audio':
        assert module in sys.modules


def test_validate_config():
    """Test validing a HIL config file."""
    config_testsuite()
    config_merge({
        'general': {
            'log_level': 'debug',
        },
        'auth': {
            'require_authentication': 'True',
        },
        'headnode': {
            'trunk_nic': 'eth0',
            'libvirt_endpoint': 'qemu:///system',
        },
        'client': {
            'endpoint': 'http://127.0.0.1:5000',
        },
        'maintenance': {
            'maintenance_project': 'maintenance',
            'url': 'http://test.xyz',
            'shutdown': '',
        },
        'extensions': {
            'hil.ext.switches.dell': '',
            'hil.ext.switches.dellnos9': '',
            'hil.ext.switches.brocade': '',
            'hil.ext.switches.n3000': '',
            'hil.ext.switches.nexus': '',
            'hil.ext.auth.null': None,
            'hil.ext.auth.keystone': '',
            'hil.ext.network_allocators.null': None,
            'hil.ext.network_allocators.vlan_pool': '',
        },
        'hil.ext.network_allocators.vlan_pool': {
            'vlans': '12, 13-20, 100-200',
        },
        'hil.ext.switches.dell': {
            'save': 'True',
        },
        'hil.ext.switches.dellnos9': {
            'save': 'False',
        },
        'hil.ext.switches.brocade': {
            'save': 'True',
        },
        'hil.ext.switches.n3000': {
            'save': 'False',
        },
        'hil.ext.switches.nexus': {
            'save': 'True',
        },
        'hil.ext.auth.keystone': {
            'auth_url': 'https://website:35357/v3',
            'auth_protocol': 'http',
            'username': 'admin',
            'password': 's3cr3t',
            'project_name': 'project',
            'admin_user': 'admin',
            'admin_password': 's3cr3t',
        }
    })
    config.load_extensions()
    config.validate_config()


def test_bool_validation_upper():
    """Test valid upper-case bools."""
    opts = ['True', 'Yes', 'On', '1', 'False', 'No', 'Off', '0']
    assert all(config.string_is_bool(s) for s in opts)


def test_bool_validation_lower():
    """Test valid lower-case bools."""
    opts = ['true', 'yes', 'on', '1', 'false', 'no', 'off', '0']
    assert all(config.string_is_bool(s) for s in opts)


def test_bool_validation_bad_cases():
    """Test invalid bools."""
    opts = ['frue', 'nes', 'yOn', '2', 'Salse', 'Go', 'bff', '3']
    assert all(not config.string_is_bool(s) for s in opts)


def test_good_web_urls():
    """Test valid (not malformed) web URLs."""
    opts = ['http://www.hil.xyz', 'https://127.0.0.1:1234', 'ftp://test.com']
    assert all(config.string_is_web_url(s) for s in opts)


def test_bad_web_urls():
    """Test malformed web URLs."""
    opts = ['http/', 'test.com', 'C:\POPUPLOG.OS2']
    assert all(not config.string_is_web_url(s) for s in opts)


def test_good_db_uris():
    """Test valid (not malformed) DB URIs."""
    opts = ['postgresql://bill:password123@localhost:1234/test',
            'sqlite:///itsadb.db']
    assert all(config.string_is_db_uri(s) for s in opts)


def test_bad_db_uris():
    """Test malformed DB URIs."""
    opts = ['https://database.com', 'postsqlite://localhost/db', 'snake']
    assert all(not config.string_is_db_uri(s) for s in opts)


def test_good_dirs():
    """Test for valid (not malformed) directories."""
    opts = ['/home/bill', '/dir', '/']
    assert all(config.string_is_dir(s) for s in opts)


def test_bad_dirs():
    """Test for malformed directories."""
    opts = ['\0', 'C:\dir', '12345']
    assert all(not config.string_is_dir(s) for s in opts)


def test_good_log_level_upper():
    """Test valid upper-case log level strings."""
    opts = ['Debug', 'Info', 'Warn', 'Warning', 'Error', 'Critical', 'Fatal']
    assert all(config.string_is_log_level(s) for s in opts)


def test_good_log_level_lower():
    """Test valid lower-case log level strings."""
    opts = ['debug', 'info', 'warn', 'warning', 'error', 'critical', 'fatal']
    assert all(config.string_is_log_level(s) for s in opts)


def test_bad_log_level_upper():
    """Test invalid log level strings."""
    opts = ['Rebug', 'Infor', 'W4rn', '12345', '\\\\\\']
    assert all(not config.string_is_log_level(s) for s in opts)


def test_good_vlans():
    "Test strings for valid VLAN ranges."""
    opts = ['12', '13,14,15,16,17,18,1234', '1-900, 902-904, 905, 1234']
    assert all(config.string_has_vlans(s) for s in opts)


def test_bad_vlans():
    "Test strings for invalid VLAN ranges."""
    opts = ['12-', 'p13,q14,15,16,17,18,1234x', '1-900, 902-904, 905, 5000']
    assert all(not config.string_has_vlans(s) for s in opts)
