from haas.dev_support import no_dry_run
from haas.config import cfg
import pytest
from haas.test_common import *

# We test two ways of using the decorator: applying it to a freestanding
# function, and applying it to an instance method.
def _function():
    @no_dry_run
    def func():
        assert False
    func()


def _method():
    class Cls:

        @no_dry_run
        def method(self):
            assert False

    obj = Cls()
    obj.method()


# We test the decorator both with the option enabled and with it disabled.
@clear_configuration
def _dry(func):
    cfg.add_section('devel')
    cfg.set('devel', 'dry_run', True)
    func()


@clear_configuration
def _wet(func):
    # The option does not exist by default, so we don't need to toggle the
    # config for this.
    with pytest.raises(AssertionError):
        func()


# Actual test cases:
def test_dry_function(): _dry(_function)
def test_wet_function(): _wet(_function)
def test_dry_method(): _dry(_method)
def test_wet_method(): _wet(_method)
