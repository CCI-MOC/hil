import unittest
from haas import cli

class TestCLI(unittest.TestCase):
    def test_wrong_arg_count(self):
        cli.run_command('create_nic 4')

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
