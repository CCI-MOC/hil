"""Tests for the `hil-admin migrate-ipmi-info` command."""

from subprocess import check_call, Popen
import shutil
import tempfile
import json
import os

import requests
import pytest

from hil.test_common import fresh_database
from hil.flaskapp import app
from hil import config, model

ADMIN_TOKEN = '01234567890123456789012345678901'
OBMD_BASE_URL = 'http://localhost:8080'


@pytest.fixture()
def tmpdir():
    """Create a temporary directory to store various files."""
    path = tempfile.mkdtemp()
    cwd = os.getcwd()
    os.chdir(path)
    yield path
    os.chdir(cwd)
    shutil.rmtree(path)


@pytest.fixture()
def configure(tmpdir):
    """Set up HIL configuration.

    This creates a hil.cfg in tmpdir, and loads it. The file needs to be
    written out separately , since we invoke other commands that read it,
    besides the test process.
    """
    cfg = '\n'.join([
        "[extensions]",
        "hil.ext.network_allocators.null =",
        "hil.ext.auth.null =",
        "hil.ext.obm.ipmi = ",
        "[devel]",
        "dry_run = True",
        "[headnode]",
        "base_imgs = base-headnode, img1, img2, img3, img4",
        "[database]",
        "uri = sqlite:///" + tmpdir + "/hil.db",
    ])
    with open(tmpdir + '/hil.cfg', 'w') as f:
        f.write(cfg)
    config.load(tmpdir + '/hil.cfg')
    config.configure_logging()
    config.load_extensions()


fresh_database = pytest.fixture(fresh_database)


@pytest.fixture()
def run_obmd(tmpdir):
    """Set up and start obmd."""
    check_call(['go', 'get', '-v', 'github.com/CCI-MOC/obmd'])

    config_file_path = tmpdir + '/obmd-config.json'

    with open(config_file_path, 'w') as f:
        f.write(json.dumps({
            'AdminToken': ADMIN_TOKEN,
            'ListenAddr': ':8080',
            'DBType': 'sqlite3',
            'DBPath': ':memory:',
        }))

    proc = Popen(['obmd', '-config', config_file_path])
    try:
        yield
    finally:
        proc.terminate()
        proc.wait()


pytestmark = pytest.mark.usefixtures('configure',
                                     'fresh_database',
                                     'run_obmd')


def test_obmd_migrate(tmpdir):
    """The test proper.

    Create some nodes, run the script, and verify that it has done the right
    thing.
    """
    from hil.ext.obm.ipmi import Ipmi

    # Add some objects to the hil database:
    with app.app_context():
        for i in range(4):
            node = model.Node(label='node-%d' % i,
                              obm=Ipmi(user='admin',
                                       host='10.0.0.%d' % (100 + i),
                                       password='changeme'))
            model.db.session.add(node)
        model.db.session.commit()

    check_call([
        'hil-admin', 'migrate-ipmi-info',
        '--obmd-base-url', OBMD_BASE_URL,
        '--obmd-admin-token', ADMIN_TOKEN,
    ])

    with app.app_context():
        for node in model.Node.query.all():

            # Check that the db info was updated correctly:
            assert node.obmd_admin_token == ADMIN_TOKEN, (
                "Node %s{label}'s admin token was incorrect: %s{token}"
                .format(
                    label=node.label,
                    token=node.obmd_admin_token,
                )
            )
            assert node.obmd_uri == OBMD_BASE_URL + '/node/' + node.label, (
                "Node %s{label}'s obmd_uri was incorrect: %s{uri}"
                .format(
                    label=node.label,
                    uri=node.obmd_uri,
                )
            )

            # Make sure obmd thinks the nodes are there; if so it should be
            # possible to get a token:
            sess = requests.Session()
            sess.auth = ('admin', ADMIN_TOKEN)
            resp = sess.post(node.obmd_uri + '/token')
            assert resp.ok, (
                "Failure getting token for node %s{label} from obmd; "
                "response: %s{resp}".format(
                    label=node.label,
                    resp=resp,
                )
            )
