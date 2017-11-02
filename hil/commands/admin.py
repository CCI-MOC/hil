"""Implement the hil-admin command."""
from hil import config, model
from hil.commands import db
from hil.commands.util import ensure_not_root
from hil.flaskapp import app
from flask.ext.script import Manager

manager = Manager(app)
manager.add_command('db', db.command)


def main():
    """Entrypoint for the hil-admin command."""
    ensure_not_root()
    config.setup()
    model.init_db()
    manager.run()
