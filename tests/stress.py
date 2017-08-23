"""Stress tests.

Tests here are catch problems like resource leaks, that only become apparent
after a certain amount of use.
"""

from hil.test_common import config_testsuite, fresh_database, config_merge, \
    fail_on_log_warnings, server_init
from hil import api, config, rest

import json
import pytest


@pytest.fixture
def configure():
    """Configure HIL"""
    config_testsuite()
    config_merge(
            {'extensions': {'hil.ext.obm.ipmi': '', }, })

    config.load_extensions()


fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)
fresh_database = pytest.fixture(fresh_database)
server_init = pytest.fixture(server_init)


pytestmark = pytest.mark.usefixtures('configure',
                                     'fresh_database',
                                     'server_init')


def test_many_http_queries():
    """Put a few objects in the db, then bombard the api with queries.

    This is intended to shake out problems like the resource leak discussed
    in issue #454.
    """
    # NOTE: Now that the session is managed by Flask-SQLAlchemy, failures here
    # are unlikely to be regressions of the issue that #454 fixed; we're no
    # longer managing the lifecycle of the session ourselves. It's not obvious
    # that this is more than clutter now, but let's not be too trigger happy
    # about deleting tests.
    with rest.app.test_request_context():
        rest.init_auth()
        api.node_register('node-99', obm={
            "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
            "host": "ipmihost",
            "user": "root",
            "password": "tapeworm"})
        api.node_register('node-98', obm={
            "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
            "host": "ipmihost",
            "user": "root",
            "password": "tapeworm"})
        api.node_register('node-97', obm={
            "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
            "host": "ipmihost",
            "user": "root",
            "password": "tapeworm"})
        api.node_register_nic('node-99', 'eth0', 'DE:AD:BE:EF:20:14')
        api.node_register_nic('node-98', 'eth0', 'DE:AD:BE:EF:20:15')
        api.node_register_nic('node-97', 'eth0', 'DE:AD:BE:EF:20:16')
        api.project_create('anvil-nextgen')
        api.project_create('anvil-legacy')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_connect_node('anvil-legacy', 'node-98')

    client = rest.app.test_client()

    def _show_nodes(path):
        """Helper for the loop below.

        This does a GET on path, which must return a json list of names of
        nodes. It will then query the state of each node. If any request does
        not return 200 or has a body which is not valid json, the test will
        fail.
        """
        resp = client.get(path)
        assert resp.status_code == 200
        for node in json.loads(resp.get_data()):
            resp = client.get('/nodes/%s' % node)
            assert resp.status_code == 200
            # At least make sure the body parses:
            json.loads(resp.get_data())

    for _i in range(100):
        _show_nodes('/nodes/free')
        resp = client.get('/projects')
        assert resp.status_code == 200
        for project in json.loads(resp.get_data()):
            _show_nodes('/project/%s/nodes' % project)
