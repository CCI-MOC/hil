from haas.config import *
import os
import tempfile
import unittest

class ConfigTest(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.mkdtemp()
        os.chdir(tmp)

    def test_missing_option(self):
        """Ensure that a missing configuration option actually caught."""
        @register_callback
        def validate():
            if not cfg.has_option('tests', 'example'):
                return False, 'option "example" in section "tests" is missing.'
            return True, None

        # Just create the file, we don't actually need to do anything to it.
        f = open('haas.cfg', 'w')
        f.close()
        self.assertRaises(BadConfigError, load)

    def test_have_needed_option_ok(self):
        """Ensure that a config with all required options is accepted."""
        @register_callback
        def validate():
            if not cfg.has_option('tests', 'example1'):
                return False, 'option "example" in section "tests" is missing.'
            return True, None

        with open('haas.cfg', 'w') as f:
            f.write('[tests]\n' +
                    'example1 = foo\n')
        load()
