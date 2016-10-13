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

from haas.dev_support import no_dry_run
import pytest
from haas.test_common import *

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


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
    config_merge({'devel': {'dry_run': True}})
    func()


def _wet(func):
    config_merge({'devel': {'dry_run': None}})
    with pytest.raises(AssertionError):
        func()


# Actual test cases:
def test_dry_function(): _dry(_function)


def test_wet_function(): _wet(_function)


def test_dry_method(): _dry(_method)


def test_wet_method(): _wet(_method)
