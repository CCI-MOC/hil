"""Unit tests for hil.ext.switches.common"""

import pytest

from hil import config
from hil.test_common import config_testsuite, config_merge


@pytest.fixture
def configure():
    """Configure HIL"""
    config_testsuite()
    config_merge({
        'auth': {
            'require_authentication': 'True',
        },
        'extensions': {
            'hil.ext.switches.brocade': '',
            'hil.ext.switches.dell': '',
        },
        'hil.ext.switches.brocade': {
            'save': 'True'
        },
        'hil.ext.switches.dell': {
            'save': 'False'
        }
    })
    config.load_extensions()


def test_parse_vlans():
    """Test parse_vlans"""
    # Have to import the method here, otherwise anything starting with
    # "hil.ext" pollutes the env.
    from hil.ext.switches.common import parse_vlans
    assert parse_vlans('12,14') == ['12', '14']
    assert parse_vlans('20-22') == ['20', '21', '22']
    assert parse_vlans('1512') == ['1512']
    assert parse_vlans('12,21-24,250,511-514') == [
            '12', '21', '22', '23', '24', '250', '511', '512', '513', '514']


def test_should_save(configure):
    """Test should save method"""
    from hil.ext.switches.brocade import Brocade
    from hil.ext.switches.dell import PowerConnect55xx
    from hil.ext.switches.common import should_save

    brocade = Brocade()
    dell = PowerConnect55xx()

    assert should_save(brocade) is True
    assert should_save(dell) is False
