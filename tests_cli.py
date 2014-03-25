import unittest
from haas import cli

class TestCLI(unittest.TestCase):
    """Test the behavior of run_command.

    run_command should never raise an exception except on exit or EOF.
    These tests are for verifying that; there are additional invariants,
    but those are not checked here.
    """
    def test_wrong_arg_count(self):
        cli.run_command('create_nic 4')

    def test_empty_cmd(self):
        # empty commands should just be ignored.
        cli.run_command('')

    def test_whitespace(self):
        # This should be treated as an empty command.
        cli.run_command('    ')

class Test_CommandClass(unittest.TestCase):
    def test_wrong_arg_count(self):
        with self.assertRaises(cli.BadCommandError):
            cli.commands['create_nic'].invoke('create_nic 4')

class TestCommandFuncs(unittest.TestCase):
    def test_usage(self):
        # at the very least, this should always return cleanly.
        cli.usage()

if __name__ == '__main__':
    unittest.main()
