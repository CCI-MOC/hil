from haas import server
from haas.migrations import command, create_db


@command.command
def create():
    """Initialize the database."""
    server.init()
    create_db()
