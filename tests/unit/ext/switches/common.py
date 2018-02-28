import pytest

from hil import config
from hil.ext.switches.common import parse_vlans, should_save
from hil.test_common import config_testsuite, config_merge
from hil.ext.switches.brocade import Brocade
from hil.ext.switches.dell import PowerConnect55xx


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
    sample_inputs = ['12,14-18,23,28,80-90', '20', '20,22', '20-22']
    assert parse_vlans('12,14') == ['12', '14']
    assert parse_vlans('20-22') == ['20', '21', '22']
    assert parse_vlans('1512') == ['1512']
    assert parse_vlans('12,21-24,250,511-514') == [
            '12', '21', '22', '23', '24', '250', '511', '512', '513', '514']


def test_should_save(configure):
    """Test should save method"""
    brocade = Brocade()
    dell = PowerConnect55xx()

    assert should_save(brocade) is True
    assert should_save(dell) is False
