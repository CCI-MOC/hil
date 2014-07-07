from haas.dev_support import no_dry_run
from haas.config import cfg
import pytest

cfg.add_section('devel')

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
def _dry(func):
    cfg.set('devel', 'dry_run', True)
    func()


def _wet(func):
    cfg.remove_option('devel', 'dry_run')
    with pytest.raises(AssertionError):
        func()

# Actual test cases:
def test_dry_function(): _dry(_function)
def test_wet_function(): _wet(_function)
def test_dry_method(): _dry(_method)
def test_wet_method(): _wet(_method)
