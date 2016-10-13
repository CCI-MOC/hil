"""Testing for migration scripts.

Only postgres is supported; if any other database backend is configured, these
tests will be skipped.

The general approach is as follows:

    1. Load a database from saved output of the `pg_dump` command.
    2. Run the migration scripts to bring it up to date.
    3. Get a dump of the resulting database. (`get_db_state()` handles this).
    4. Clear the database, and freshly initialize it (with the latest version
       of the schema
    5. Populate the database with a specific set of objects.
    6. Get a dumpof the resulting databse.
    7. Compare the two dumps. They should be the same.

"""
import pytest
from haas import server
from haas.test_common import config_testsuite, config_merge, initial_db, \
    fail_on_log_warnings
from haas.config import cfg, load_extensions
from haas.model import db, init_db
from haas.flaskapp import app
from haas.migrations import create_db
from flask_migrate import upgrade
from os import path
import re
from pprint import pformat
import difflib

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


# Directory containing database dumps (./migrations)
pg_dump_dir = path.join(path.dirname(__file__), "migrations")


def drop_tables():
    """Drop all the tables in the database.

    This is distinct from db.drop_all() in that it isn't dependent on what
    SQLAlchemy thinks the schema should be; it just gets all the table names
    and drops them. This is important since in these test we are working
    with older versions of the schema.
    """
    # Notes about the implementation:
    #
    # * SQLAlchemy's inspector can do a bit more than we're using it for here;
    #   however, after fighting with all of the nitty-gritty details of
    #   using it to construct a metadata object that would let us just do a
    #   call to drop_all(), it was decided that it wsan't worth the trouble.
    # * The below constructs a raw SQL string programmatically. In general,
    #   this should set off your spidey-sense, and is not condoned outside of
    #   the test suite, or without _very_ careful consideration even within it.
    #   However, in this case the inputs are controlled, so there is no risk
    #   of malicious input. Furthermore, per the first bullet point, this was
    #   far simpler than convincing SQLAlchemy to do the right thing.
    tablenames = db.inspect(db.engine).get_table_names()
    for tablename in tablenames:
        db.session.execute('DROP TABLE IF EXISTS "' +
                           tablename + '" CASCADE')
    db.session.commit()


@pytest.fixture(autouse=True)
def configure():
    config_testsuite()
    if not cfg.get('database', 'uri').startswith('postgresql:'):
        pytest.skip('Database migrations are only supported for postgresql.')
    init_db()


def load_dump(filename):
    """Load a database dump and upgrades it to the latest schema.

    `filename` is path to the SQL dump to load, relative to `pg_dump_dir`.

    The SQL in that file will be executed, and then migration scripts will
    be run to bring it up to date.
    """
    with open(path.join(pg_dump_dir, filename)) as f:
        sql = f.read()
    with app.app_context():
        db.session.execute(sql)
        db.session.commit()
    upgrade(revision='heads')


def fresh_create():
    """Create a fresh database, and populate it with an initial set of objects.

    The objects are created via `initial_db`. These objects should be such that
    a migrated database dump will have the same contents.
    """
    create_db()
    initial_db()


def get_db_state():
    """Inspect the database, and return a representation of its contents

    The return value is a dictionary mapping table names to dictionaries
    containing two keys each:

        - 'schema', which describes the columns for that table.
        - 'rows', which is a list of all rows in the table.
    """
    result = {}
    inspector = db.inspect(db.engine)
    metadata = db.MetaData()

    for name in inspector.get_table_names():
        schema = inspector.get_columns(name)
        tbl = db.Table(name, metadata)
        inspector.reflecttable(tbl, None)
        rows = db.session.query(tbl).all()
        result[name] = {
            'schema': schema,
            'rows': sorted(rows),
        }

    return result


@pytest.mark.parametrize('filename,extra_config', [
    ['flask.sql', {
        'extensions': {
            'haas.ext.switches.mock': '',
            'haas.ext.switches.nexus': '',
            'haas.ext.switches.dell': '',
            'haas.ext.obm.ipmi': '',
            'haas.ext.obm.mock': '',
            'haas.ext.auth.database': '',
            'haas.ext.network_allocators.vlan_pool': '',

            # These are on by default; disable them.
            'haas.ext.auth.null': None,
            'haas.ext.network_allocators.null': None,
        },
        'haas.ext.network_allocators.vlan_pool': {
            'vlans': '100-200, 300-500',
        },
    }],
])
def test_db_eq(filename, extra_config):
    """Verify that each function in fns creates the same database."""

    config_merge(extra_config)
    load_extensions()
    server.register_drivers()
    server.validate_state()

    def run_fn(f):
        """Run the function f and return a representation of its db."""

        # We can't just do db.drop_all(), since db's metadata won't
        # necessarily reflect the contents of the database. If there are
        # tables it doesn't know about, it may raise an exception.
        with app.app_context():
            drop_tables()
            f()

        return get_db_state()

    upgraded = run_fn(lambda: load_dump(filename))
    fresh = run_fn(fresh_create)
    drop_tables()

    def censor_nondeterminism(string):
        """Censor parts of the output whose values are non-deterministic.

        Certain objects (currently just uuids) are generated
        non-deterministically, and will thus be different between databases
        even if everything is working. This function censors the relevant
        parts of `string`, so that they don't cause the tests to fail.
        """
        hex_re = r'[0-9a-f]'
        uuid_re = hex_re * 8 + ('-' + hex_re * 4) * 3 + '-' + hex_re * 12
        return re.sub(uuid_re, '<<UUID>>', string)

    differ = difflib.Differ()
    upgraded = censor_nondeterminism(pformat(upgraded)).split('\n')
    fresh = censor_nondeterminism(pformat(fresh)).split('\n')

    assert upgraded == fresh, (
        "Databases are different!\n\n" +
        pformat(list(differ.compare(upgraded, fresh)))
    )
