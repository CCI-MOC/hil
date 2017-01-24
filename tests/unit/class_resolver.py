import haas
from haas.class_resolver import *
from haas.model import *
from haas.test_common import fail_on_log_warnings
import pytest

mockapi_name = 'http://schema.massopencloud.org/haas/v0/'
fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


@pytest.fixture(autouse=True)
def mock_extensions():
    from haas.ext.obm import mock
    from haas.ext.switches import mock


class Food(object):
    pass


class Apple(Food):
    api_name = 'apple'


class Orange(Food):
    api_name = 'orange'


class Drink(object):
    pass


class Juice(Drink):
    pass


class OrangeJuice(Juice):
    api_name = 'orange'


class _AppleJuice(Juice):
    # _AppleJuice is an implementation detail; we don't give it
    # an ``api_name`` because we don't want to expose it to users... for some
    # reason.
    pass


class GrapeJuice(Juice):
    api_name = 'grape'


def test_class_resolver():
    build_class_map_for(Food)
    build_class_map_for(Drink)

    assert concrete_class_for(Food, 'apple') is Apple
    assert concrete_class_for(Food, 'orange') is Orange
    assert concrete_class_for(Food, 'grape') is None
    assert concrete_class_for(Drink, 'apple') is None
    assert concrete_class_for(Drink, 'orange') is OrangeJuice
    assert concrete_class_for(Drink, 'grape') is GrapeJuice


def test_class_Obm():
    build_class_map_for(Obm)
    assert concrete_class_for(Obm, mockapi_name+"obm/mock") \
        is haas.ext.obm.mock.MockObm


def test_class_Switch():
    build_class_map_for(Switch)
    assert concrete_class_for(Switch, mockapi_name+"switches/mock") \
        is haas.ext.switches.mock.MockSwitch
