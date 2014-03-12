import unittest
from haas import cli

class TestCLI(unittest.TestCase):

    def test_wrong_arg_count(self):
        cli.run_command('create_nic 4')

if __name__ == '__main__':
    unittest.main()
