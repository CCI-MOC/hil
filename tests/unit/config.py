"""Test the hil.config module."""
from hil.test_common import config_set, fail_on_log_warnings
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
