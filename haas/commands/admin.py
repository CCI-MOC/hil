from haas import config, migrations, model, server
from haas.flaskapp import app
from flask.ext.script import Manager

manager = Manager(app)
manager.add_command('migrate', migrations.command)


@manager.command
def create_db():
    """Initialize the database."""
    server.init()
    migrations.create_db()


def main():
    """Entrypoint for the haas-admin command."""
    config.load()
    config.configure_logging()
    config.load_extensions()
    model.init_db()
    manager.run()
