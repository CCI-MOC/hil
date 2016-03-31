from haas import config, model
from haas.commands import db
from haas.flaskapp import app
from flask.ext.script import Manager

manager = Manager(app)
manager.add_command('db', db.command)


def main():
    """Entrypoint for the haas-admin command."""
    config.setup()
    model.init_db()
    manager.run()
