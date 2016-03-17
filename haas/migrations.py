from flask_migrate import Migrate, MigrateCommand, stamp
from haas.flaskapp import app
from haas.model import db
from haas.network_allocator import get_network_allocator
from os.path import join, dirname

migrate = Migrate(app, db,
                  # Use the package's directory. This ensures that the
                  # migration scripts are available when the package is
                  # installed system-wide:
                  directory=join(dirname(__file__), 'migrations'))
command = MigrateCommand


def create_db():
    """Create and populate the initial database.

    The database connection must have been previously initialzed via `haas.model.init_db`.
    """
    with app.app_context():
        db.create_all()
        stamp()
        get_network_allocator().populate()
        db.session.commit()
