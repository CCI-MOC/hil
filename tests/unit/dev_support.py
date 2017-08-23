# Copyright 2013-2014 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.
"""Test the hil.dev_support module."""

from hil.dev_support import no_dry_run
import pytest
from hil.test_common import fail_on_log_warnings, config_merge

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


# We test two ways of using the decorator: applying it to a freestanding
# function, and applying it to an instance method.


def _function():
    """Helper which uses no_dry_run on a plain function."""
    @no_dry_run
    def func():
        """Assert false, so we can check if the function is called."""
        assert False
    func()


def _method():
    """Helper which uses no_dry_run on a method."""
    class Cls:
        """Test class to carry the method."""

        @no_dry_run
        def method(self):
            """Assert false, so we can check if the method is called."""
            assert False

    obj = Cls()
    obj.method()


# We test the decorator both with the option enabled and with it disabled.
def _dry(func):
    """Call ``func`` with dry_run enabled."""
    config_merge({'devel': {'dry_run': True}})
    func()


def _wet(func):
    """Call ``func`` with dry_run disabled."""
    config_merge({'devel': {'dry_run': None}})
    with pytest.raises(AssertionError):
        func()


# Actual test cases:
def test_dry_function():
    """Test dry_run enabled on a function."""
    _dry(_function)


def test_wet_function():
    """Test dry_run disabled on a function."""
    _wet(_function)


def test_dry_method():
    """Test dry_run enabled on a method."""
    _dry(_method)


def test_wet_method():
    """Test dry_run disabled on a method."""
    _wet(_method)
