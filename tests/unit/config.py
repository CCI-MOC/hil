from haas.test_common import config_set
from haas import config
import sys


def test_load_extension():
    """Check that putting modules in [extensions] results in importing them."""
    config_set({
        'extensions': {
            # These modules are chosen because:
            #
            # 1. They are in the standard library, and cross-platform
            # 2. If you ever think you need to import these for use in
            #    HaaS, I will judge you.
            'sndhdr': '',
            'colorsys': '',
            'email.mime.audio': '',
        },
    })
    config.load_extensions()
    for module in 'sndhdr', 'colorsys', 'email.mime.audio':
        assert module in sys.modules
