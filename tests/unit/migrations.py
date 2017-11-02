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
from hil import api, model, server
from hil.test_common import config_testsuite, config_merge, initial_db, \
    fail_on_log_warnings
from hil.config import cfg, load_extensions
from hil.model import db, init_db
from hil.flaskapp import app
from hil.migrations import create_db
from hil.rest import local
from flask_migrate import upgrade
from os import path
import re
from pprint import pformat
import difflib

MOCK_SWITCH_TYPE = 'http://schema.massopencloud.org/haas/v0/switches/mock'
MOCK_OBM_TYPE = 'http://schema.massopencloud.org/haas/v0/obm/mock'


def create_pending_actions_db():
    """Create database objects including a pending NetworkingAction.

    The first version of this function was used to create the dump
    'pending-networking-actions.sql'.
    """
    # At a minimum we need a project, node, nic, switch, port, and network:
    api.project_create('runway')
    api.node_register(
        'node-1',
        obm={
            'type': MOCK_OBM_TYPE,
            'user': 'user',
            'host': 'host',
            'password': 'pass',
        },
    )
    api.node_register_nic('node-1', 'pxe', 'de:ad:be:ef:20:16')
    api.switch_register('sw0',
                        type=MOCK_SWITCH_TYPE,
                        username='user',
                        hostname='host',
                        password='pass',
                        )
    api.switch_register_port('sw0', 'gi1/0/4')
    api.port_connect_nic('sw0', 'gi1/0/4', 'node-1', 'pxe')
    api.project_connect_node('runway', 'node-1')
    api.network_create('runway_pxe', 'runway', 'runway', '')

    # Queue up a networking action. Importantly, we do *not* call
    # deferred.apply_networking, as that would flush the action and
    # remove it from the database.
    api.node_connect_network('node-1', 'pxe', 'runway_pxe')


def create_bigint_db():
    """Create database objects used in 'after-PK-bigint.sql'"""
    from hil.ext.switches.n3000 import DellN3000
    from hil.ext.switches.dell import PowerConnect55xx
    from hil.ext.switches.brocade import Brocade
    from hil.ext.switches.nexus import Nexus
    from hil.ext.switches.mock import MockSwitch
    from hil.ext.obm.ipmi import Ipmi
    from hil.ext.obm.mock import MockObm
    from hil.ext.auth.database import User
    from hil.ext.auth import database as dbauth
    with app.app_context():
        db.session.add(DellN3000(label='sw-n3000',
                                 hostname='host',
                                 username='user',
                                 password='pass',
                                 dummy_vlan='5',
                                 type=DellN3000.api_name))
        dell1 = PowerConnect55xx(label='sw-dell',
                                 hostname='host',
                                 username='user',
                                 password='pass',
                                 type=PowerConnect55xx.api_name)
        db.session.add(dell1)
        db.session.add(Nexus(label='sw-nexus',
                             hostname='host',
                             username='user',
                             password='pass',
                             dummy_vlan='5',
                             type=Nexus.api_name))
        db.session.add(Brocade(label='sw-brocade',
                               hostname='host',
                               username='user',
                               password='pass',
                               interface_type='4',
                               type=Brocade.api_name))
        db.session.add(MockSwitch(label='sw0',
                                  hostname='host',
                                  username='user',
                                  password='pass',
                                  type=MockSwitch.api_name))
        proj = model.Project(label='runway')
        db.session.add(proj)
        headnode1 = model.Headnode(label='runway_headnode',
                                   project=proj,
                                   base_img='image1')
        db.session.add(headnode1)
        db.session.add(model.Hnic(label='hnic1',
                                  headnode=headnode1))
        ipmi = Ipmi(host='host',
                    user='user',
                    password='pass')
        db.session.add(ipmi)
        mock_obm = MockObm(host='host',
                           user='user',
                           password='pass')
        db.session.add(mock_obm)
        node1 = model.Node(label='node-1',
                           obm=ipmi)
        db.session.add(node1)

        db.session.add(model.Metadata(label='meta',
                                      value="it is a true value",
                                      node=node1))
        network1 = model.Network(owner=None,
                                 access=[proj],
                                 allocated=False,
                                 network_id="networking network",
                                 label='hil wireless')
        db.session.add(network1)
        nic1 = model.Nic(node=node1,
                         label='pxe',
                         mac_addr='ff:ff:ff:ff:ff:fe')
        model.Port(label='A fine port',
                   switch=dell1)
        db.session.add(nic1)
        db.session.add(model.NetworkAttachment(nic=nic1,
                                               network_id=1,
                                               channel='vlan/100'))
        db.session.add(model.NetworkingAction(type='modify_port',
                                              nic=nic1,
                                              new_network=network1,
                                              channel='vlan/100'))
        jim = User(label='jim',
                   password='heyimjim',
                   is_admin=True)
        db.session.add(jim)

        local.auth = dbauth.User.query.filter_by(label='jim').one()

        dbauth.user_add_project('jim', 'runway')

        db.session.commit()

        # Original password is "pass"
        db.session.query(User).get(1).hashed_password = \
            ('$6$rounds=656000$iTyrApYTUhMx4b4g$YcaMExV'
             'YtS0ut2yXWrT64OggFpE4lLg12QsAuyMA3YKX6Czth'
             'XeisA47dJZW9GwU2q2CTIVrsbpxAVT64Pih2/')
        db.session.commit()

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
    """Configure HIL, and test which db we're using.

    Skips the test unless we're using postgres.
    """
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


def fresh_create(make_objects):
    """Create a fresh database, and populate it with an initial set of objects.

    The objects are created via `make_objects`. These objects should be such
    that a migrated database dump will have the same contents.
    """
    create_db()
    make_objects()


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

        # the inspector gives us the schema as a list, and the rows
        # as a list of tuples. the columns in each row are matched
        # up with the schema by position, but this may vary
        # (acceptably) depending on when migration scripts are run.
        # So, we normalize this by converting both to dictionaries
        # with the column names as keys.
        row_dicts = []
        for row in rows:
            row_dicts.append({})
            for i in range(len(row)):
                row_dicts[-1][schema[i]['name']] = row[i]

        schema = dict((col['name'], col) for col in schema)

        result[name] = {
            'schema': schema,
            'rows': sorted(row_dicts),
        }

    return result


@pytest.mark.parametrize('filename,make_objects,extra_config', [
    ['after-PK-bigint.sql', create_bigint_db, {
        'extensions': {
            'hil.ext.switches.mock': '',
            'hil.ext.switches.nexus': '',
            'hil.ext.switches.dell': '',
            'hil.ext.switches.n3000': '',
            'hil.ext.switches.brocade': '',
            'hil.ext.obm.ipmi': '',
            'hil.ext.obm.mock': '',
            'hil.ext.auth.database': '',
            'hil.ext.network_allocators.vlan_pool': '',

            # These are on by default; disable them.
            'hil.ext.auth.null': None,
            'hil.ext.network_allocators.null': None,
        },
        'hil.ext.network_allocators.vlan_pool': {
            'vlans': '100-200, 300-500',
        },
    }],
    ['flask.sql', initial_db, {
        'extensions': {
            'hil.ext.switches.mock': '',
            'hil.ext.switches.nexus': '',
            'hil.ext.switches.dell': '',
            'hil.ext.obm.ipmi': '',
            'hil.ext.obm.mock': '',
            'hil.ext.auth.database': '',
            'hil.ext.network_allocators.vlan_pool': '',

            # These are on by default; disable them.
            'hil.ext.auth.null': None,
            'hil.ext.network_allocators.null': None,
        },
        'hil.ext.network_allocators.vlan_pool': {
            'vlans': '100-200, 300-500',
        },
    }],
    ['pending-networking-actions.sql', create_pending_actions_db, {
        'extensions': {
            'hil.ext.obm.mock': '',
            'hil.ext.switches.mock': '',
            'hil.ext.auth.null': '',
            'hil.ext.network_allocators.null': '',
        },
    }],
])
def test_db_eq(filename, make_objects, extra_config):
    """Migrating from a snapshot should create the same objects as a new db.

    `make_objects` is a function that, when run against the latest version
        of a schema, will create some set of objects.
    `filename` is the name of an sql dump of a previous database, whose
        contents were created with the then-current version of `make_objects`.
    `extra_config` specifies modifications to the hil.cfg under which the
        test is run. this is passed to `config_merge`.

    The test does the following:

        * Restore the database snapshot and run the migration scripts to update
          its contents to the current schema.
        * Create a fresh database according to the current schema, and execute
          `make_objects`.
        * Compare the two resulting databases. The test passes if and only if
          they are the same.
    """

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
    fresh = run_fn(lambda: fresh_create(make_objects))
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
