"""Database migration support.

Contains code for:

* adding migration related commands to the hil-admin cli
* initializing alembic
* validating the database schema
"""
from flask_migrate import Migrate, MigrateCommand
from hil.flaskapp import app
from hil.model import db
from hil.network_allocator import get_network_allocator
from os.path import join, dirname
import sys

from alembic.config import Config
from alembic.script import ScriptDirectory

# This is a dictionary mapping the names of modules to directories containing
# their alembic version scripts. Extensions may add entries to this with their
# own module names as keys.
#
# Extensions which use this facility must also use their module name as a
# a branch_label on their migration scripts.
paths = {
    'hil': join(dirname(__file__), 'migrations', 'versions'),
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

    # It is important that the entry for HIL core ('hil') is first; I(zenhack)
    # assume this has something to do with search order, but this hangs
    # otherwise.
    paths_scratch = paths.copy()
    core_path = paths_scratch.pop('hil')
    configval = ' '.join([core_path] + list(paths_scratch.values()))

    config.set_main_option('version_locations', configval)
    return config


# Alembic will create this table itself if need be when doing "stamp" in the
# create_db  function below, but unless we declare it, db.drop_all() won't
# know about it, and will leave us with a one-table database.
AlembicVersion = db.Table(
    'alembic_version', db.metadata,
    db.Column('version_num', db.String(32), nullable=False)
)


def _expected_heads():
    cfg_path = join(dirname(__file__), 'migrations',  'alembic.ini')
    cfg = Config(cfg_path)
    _configure_alembic(cfg)
    cfg.set_main_option('script_location', dirname(cfg_path))
    script_dir = ScriptDirectory.from_config(cfg)
    return set(script_dir.get_heads())


def create_db():
    """Create and populate the initial database.

    The database connection must have been previously initialzed via
    `hil.model.init_db`.
    """
    with app.app_context():
        db.create_all()
        for head in _expected_heads():
            # Record the version of each branch. Each extension which uses the
            # database will have its own branch.
            db.session.execute(
                AlembicVersion.insert().values(version_num=head)
            )
        get_network_allocator().populate()
        db.session.commit()


def check_db_schema():
    """Verify that the database schema is present and up-to-date.

    If not, an error message is printed and the program is aborted.
    """
    tablenames = db.inspect(db.engine).get_table_names()

    if 'alembic_version' not in tablenames:
        sys.exit("ERROR: Database schema is not initialized; have you run "
                 "hil-admin db create?")

    actual_heads = {row[0] for row in
                    db.session.query(AlembicVersion).all()}

    if _expected_heads() != actual_heads:
        sys.exit("ERROR: Database schema version is incorrect; try "
                 "running hil-admin db upgrade heads.")
