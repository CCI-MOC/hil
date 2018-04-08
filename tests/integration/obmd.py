import tempfile
import os
import json
import requests
import pytest
from subprocess import Popen
from hil.test_common import config_testsuite, config_merge, \
    fresh_database, fail_on_log_warnings, server_init, with_request_context

from hil import api, config, errors


@pytest.fixture()
def configure():
    config_testsuite()
    config_merge({
        'extensions': {
            'hil.ext.obm.mock': '',
        },
        'devel': {
            'dry_run': None,
        },
    })
    config.load_extensions()


fresh_database = pytest.fixture(fresh_database)
fail_on_log_warnings = pytest.fixture(fail_on_log_warnings)
server_init = pytest.fixture(server_init)
with_request_context = pytest.yield_fixture(with_request_context)


pytestmark = pytest.mark.usefixtures(
    'configure',
    'fresh_database',
    'fail_on_log_warnings',
    'server_init',
    'with_request_context',
)


@pytest.fixture
def obmd_cfg():
        cfg = {
            'ListenAddr': ":8833",
            'AdminToken': "8fcfe5d3f8ca8c4b87d0f8ae86b43bca",
            'DBType': 'sqlite3',
            'DBPath': ':memory:',
        }

        (fd, name) = tempfile.mkstemp()
        os.write(fd, json.dumps(cfg))
        os.close(fd)
        obmd_proc = Popen(['obmd', '-config', name])

        yield cfg

        obmd_proc.terminate()
        obmd_proc.wait()
        os.remove(name)


def test_enable_disable_obm(obmd_cfg):
    obmd_uri = 'http://localhost' + obmd_cfg['ListenAddr'] + '/node/node-99'

    # register a node with obmd:
    requests.put(
        obmd_uri,
        auth=('admin', obmd_cfg['AdminToken']),
        data=json.dumps({
            "type": "ipmi",
            "info": {
                "addr": "10.0.0.4",
                "user": "ipmuser",
                "pass": "ipmipass",
            },
        }))

    # and then with hil:
    api.node_register(
        node='node-99',
        obm={
            "type": 'http://schema.massopencloud.org/haas/v0/obm/mock',
            "host": "ipmihost",
            "user": "root",
            "password": "tapeworm",
        },
        obmd={
            'uri': obmd_uri,
            'admin_token': obmd_cfg['AdminToken'],
        },
    )

    # Then create a project, and attach the node.
    api.project_create('anvil-nextgen')
    api.project_connect_node('anvil-nextgen', 'node-99')

    # now the test proper:

    # First, enable the obm
    api.node_enable_disable_obm('node-99', enabled=True)

    # Obm is enabled; we shouldn't be able to detach the node:
    with pytest.raises(errors.BlockedError):
        api.project_detach_node('anvil-nextgen', 'node-99')

    # ...so disable it first:
    api.node_enable_disable_obm('node-99', enabled=False)

    # ...and then it should work:
    api.project_detach_node('anvil-nextgen', 'node-99')
