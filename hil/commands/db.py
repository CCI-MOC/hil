"""Implement the ``hil-admin db`` subcommand."""
from hil import server
from hil.migrations import command, create_db


@command.command
def create():
    """Initialize the database."""
    server.init()
    create_db()
