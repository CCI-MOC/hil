"""Helpers used in various commands."""
import os
import sys


def ensure_not_root():
    """
    Verify that we aren't running as root, exiting with an error otherwise.
    """
    if os.getuid() == 0:
        sys.exit("You're running %s as root. Don't do this -- use "
                 "a regular user account. Exiting." % sys.argv[0])
