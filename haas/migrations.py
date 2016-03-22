from flask_migrate import Migrate, MigrateCommand, stamp
from haas.flaskapp import app
from haas.model import db
from haas.network_allocator import get_network_allocator
from os.path import join, dirname

# This is a dictionary mapping the names of modules to directories containing
# their alembic version scripts. Extensions may add entries to this with their
# own module names as keys.
#
# Extensions which use this facility must also use their module name as a
# a branch_label on their migration scripts.
paths = {
    'haas': join(dirname(__file__), 'migrations', 'versions'),
}

migrate = Migrate(app, db,
                  # Use the package's directory. This ensures that the
                  # migration scripts are available when the package is
                  # installed system-wide:
                  directory=join(dirname(__file__), 'migrations'))
command = MigrateCommand


@migrate.configure
def _configure_alembic(config):
    """Customize alembic configuration."""
    # Configure the path for version scripts to include all of the directories
    # named in the `paths` dictionary, above:
    config.set_main_option('version_locations',
                           ' '.join(paths.values()))
    return config


def create_db():
    """Create and populate the initial database.

    The database connection must have been previously initialzed via `haas.model.init_db`.
    """
    with app.app_context():
        db.create_all()
        for head in paths.keys():
            stamp(revision=head)
        get_network_allocator().populate()
        db.session.commit()
