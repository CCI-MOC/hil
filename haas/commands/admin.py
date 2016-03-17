from haas import config, model
from haas.commands import db
from haas.flaskapp import app
from flask.ext.script import Manager

manager = Manager(app)
manager.add_command('db', db.command)


def main():
    """Entrypoint for the haas-admin command."""
    config.load()
    config.configure_logging()
    config.load_extensions()
    model.init_db()
    manager.run()
