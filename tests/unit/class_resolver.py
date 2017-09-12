"""Test the hil.class_resolver module."""
import hil
from hil.class_resolver import concrete_class_for, build_class_map_for
from hil import model
from hil.test_common import fail_on_log_warnings
import pytest

mockapi_name = 'http://schema.massopencloud.org/haas/v0/'
fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


@pytest.fixture(autouse=True)
def mock_extensions():
    """Import the mock drivers.

    Just used for the side-effect of registering the subclasses.
    """
    # pylint: disable=unused-variable
    import hil.ext.obm.mock
    import hil.ext.switches.mock


class Food(object):
    """A superclass to test with class_resolver"""


class Apple(Food):
    """A subclass to test with class_resolver"""
    api_name = 'apple'


class Orange(Food):
    """A subclass to test with class_resolver"""
    api_name = 'orange'


class Drink(object):
    """A superclass to test with class_resolver"""


class Juice(Drink):
    """A subclass to test with class_resolver"""


class OrangeJuice(Juice):
    """A subclass to test with class_resolver"""
    api_name = 'orange'


class _AppleJuice(Juice):
    """A subclass with no api_name, to test with class_resolver"""
    # _AppleJuice is an implementation detail; we don't give it
    # an ``api_name`` because we don't want to expose it to users... for some
    # reason.


class GrapeJuice(Juice):
    """A subclass to test with class_resolver"""
    api_name = 'grape'


def test_class_resolver():
    """Test class_resolver with our test classes, above."""
    build_class_map_for(Food)
    build_class_map_for(Drink)

    assert concrete_class_for(Food, 'apple') is Apple
    assert concrete_class_for(Food, 'orange') is Orange
    assert concrete_class_for(Food, 'grape') is None
    assert concrete_class_for(Drink, 'apple') is None
    assert concrete_class_for(Drink, 'orange') is OrangeJuice
    assert concrete_class_for(Drink, 'grape') is GrapeJuice


def test_class_Obm():
    """Test class_resolver with MockObm"""
    build_class_map_for(model.Obm)
    assert concrete_class_for(model.Obm, mockapi_name + "obm/mock") \
        is hil.ext.obm.mock.MockObm


def test_class_Switch():
    """Test class_resolver with MockSwitch"""
    build_class_map_for(model.Switch)
    assert concrete_class_for(model.Switch, mockapi_name + "switches/mock") \
        is hil.ext.switches.mock.MockSwitch
