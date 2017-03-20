# Copyright 2013-2014 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

"""Unit tests for client library"""
import haas
from haas import model, api, deferred, server, config
from haas.model import db
from haas.network_allocator import get_network_allocator
import pytest
import json
import requests
import os
import tempfile
import subprocess
import time
from subprocess import check_call, Popen
from urlparse import urljoin
import requests
from requests.exceptions import ConnectionError
from haas.client.base import ClientBase
from haas.client.auth import db_auth
from haas.client.client import Client
from haas.client import errors


ep = "http://127.0.0.1:8000" or os.environ.get('HAAS_ENDPOINT')
username = "hil_user" or os.environ.get('HAAS_USERNAME')
password = "hil_pass1234" or os.environ.get('HAAS_PASSWORD')

sess = db_auth(username, password)
C = Client(ep, sess)  # Initializing client library
MOCK_SWITCH_TYPE = 'http://schema.massopencloud.org/haas/v0/switches/mock'
OBM_TYPE_MOCK = 'http://schema.massopencloud.org/haas/v0/obm/mock'
OBM_TYPE_IPMI = 'http://schema.massopencloud.org/haas/v0/obm/ipmi'


# Following tests check if the client library is initialized correctly

def test_db_auth():
    sess = db_auth(username, password)
    assert sess.auth == (username, password)


class Test_ClientBase:
    """ When the username, password is not defined
    It should raise a LookupError
    """

    def test_init_error(self):
        try:
            x = ClientBase()
        except TypeError:
            assert True

# FIX ME: The test may vary based on which backend session is used.
#    def test_correct_init(self):
#        x = ClientBase(ep, 'some_base64_string')
#        assert x.endpoint == "http://127.0.0.1:8000"
#        assert x.auth == "some_base64_string"

    def test_object_url(self):
        x = ClientBase(ep, 'some_base64_string')
        y = x.object_url('abc', '123', 'xy23z')
        assert y == 'http://127.0.0.1:8000/abc/123/xy23z'

# For testing the client library we need a running HIL server, with dummy
# objects populated. Following classes accomplish that end.
# It shall:
#       1. Configures haas.cfg
#       2. Instantiates a database
#       3. Starts a server on an arbitary port
#       4. Populates haas with dummy objects
#       5. tears down the setup in a clean fashion.


# pytest.fixture(scope="module")

def make_config():
    """ This function creates haas.cfg with desired options
    and writes to a temporary directory.
    It returns a tuple where (tmpdir, cwd) = ('location of haas.cfg', 'pwdd')
    """
    tmpdir = tempfile.mkdtemp()
    cwd = os.getcwd()
    os.chdir(tmpdir)
    with open('haas.cfg', 'w') as f:
        config = '\n'.join([
            '[general]',
            '[devel]',
            'dry_run=True',
            '[auth]',
            'require_authentication = True',

            '[headnode]',
            'base_imgs = base-headnode, img1, img2, img3, img4',
            '[database]',
            'uri = sqlite:///%s/haas.db' % tmpdir,
            '[extensions]',
            'haas.ext.auth.database =',
            'haas.ext.switches.mock =',
            'haas.ext.switches.nexus =',
            'haas.ext.switches.dell =',
            'haas.ext.switches.brocade =',
            'haas.ext.obm.mock =',
            'haas.ext.obm.ipmi =',
            'haas.ext.network_allocators.vlan_pool =',
            '[haas.ext.network_allocators.vlan_pool]',
            'vlans = 1001-1040',

        ])
        f.write(config)
        return (tmpdir, cwd)


def cleanup((tmpdir, cwd)):
    """ Cleanup crew, when all tests are done.
    It will shutdown the haas server,
    delete any files and folders created for the tests.
    """

    os.remove('haas.cfg')
    os.remove('haas.db')
    os.chdir(cwd)
    os.rmdir(tmpdir)


def initialize_db():
    """ Creates an  database as defined in haas.cfg."""
    check_call(['haas-admin', 'db', 'create'])
    check_call(['haas', 'create_admin_user', username, password])


def run_server(cmd):
    """This function starts a haas server.
    The arguments in 'cmd' will be a list of arguments like required to start a
    haas server like ['haas', 'serve', '8000']
    It will return a handle which can be used to terminate the server when
    tests finish.
    """
    proc = Popen(cmd)
    return proc


def populate_server():
    """
    Once the server is started, this function will populate some mock objects
    to faciliate testing of the client library
    """
    sess = requests.Session()
    sess.auth = (username, password)

    # Adding nodes, node-01 - node-06
    url_node = 'http://127.0.0.1:8000/node/'
    api_nodename = 'http://schema.massopencloud.org/haas/v0/obm/'

    for i in range(1, 10):
        obminfo = {
                "type": api_nodename + 'ipmi', "host": "10.10.0.0"+repr(i),
                "user": "ipmi_u", "password": "pass1234"
                }
        sess.put(
                url_node + 'node-0'+repr(i), data=json.dumps({"obm": obminfo})
                )
        sess.put(
                url_node + 'node-0' + repr(i) + '/nic/eth0', data=json.dumps(
                            {"macaddr": "aa:bb:cc:dd:ee:0" + repr(i)}
                            )
                     )

    # Adding Projects proj-01 - proj-03
    for i in ["proj-01", "proj-02", "proj-03"]:
        sess.put('http://127.0.0.1:8000/project/' + i)

    # Adding switches one for each driver
    url_switch = 'http://127.0.0.1:8000/switch/'
    api_name = 'http://schema.massopencloud.org/haas/v0/switches/'

    dell_param = {
            'type': api_name + 'powerconnect55xx', 'hostname': 'dell-01',
            'username': 'root', 'password': 'root1234'
            }
    nexus_param = {
            'type': api_name + 'nexus', 'hostname': 'nexus-01',
            'username': 'root', 'password': 'root1234', 'dummy_vlan': '333'
            }
    mock_param = {
            'type': api_name + 'mock', 'hostname': 'mockSwitch-01',
            'username': 'root', 'password': 'root1234'
            }
    brocade_param = {
            'type': api_name + 'brocade', 'hostname': 'brocade-01',
            'username': 'root', 'password': 'root1234',
            'interface_type': 'TenGigabitEthernet'
            }

    sess.put(url_switch + 'dell-01', data=json.dumps(dell_param))
    sess.put(url_switch + 'nexus-01', data=json.dumps(nexus_param))
    sess.put(url_switch + 'mock-01', data=json.dumps(mock_param))
    sess.put(url_switch + 'brocade-01', data=json.dumps(brocade_param))

    # Adding ports to the mock switch, Connect nics to ports:
    for i in range(1, 8):
        sess.put(url_switch + 'mock-01/port/gi1/0/' + repr(i))
        sess.post(
                url_switch + 'mock-01/port/gi1/0/' + repr(i) + '/connect_nic',
                data=json.dumps(
                    {'node': 'node-0' + repr(i), 'nic': 'eth0'}
                    )
                )

# Adding port gi1/0/8 to switch mock-01 without connecting it to any node.
    sess.put(url_switch + 'mock-01/port/gi1/0/8')

    # Adding Projects proj-01 - proj-03
    for i in ["proj-01", "proj-02", "proj-03"]:
        sess.put('http://127.0.0.1:8000/project/' + i)

    # Allocating nodes to projects
    url_project = 'http://127.0.0.1:8000/project/'
    # Adding nodes 1 to proj-01
    sess.post(
            url_project + 'proj-01' + '/connect_node',
            data=json.dumps({'node': 'node-01'})
            )
    # Adding nodes 2, 4 to proj-02
    sess.post(
            url_project + 'proj-02' + '/connect_node',
            data=json.dumps({'node': 'node-02'})
            )
    sess.post(
            url_project + 'proj-02' + '/connect_node',
            data=json.dumps({'node': 'node-04'})
            )
    # Adding node  3, 5 to proj-03
    sess.post(
            url_project + 'proj-03' + '/connect_node',
            data=json.dumps({'node': 'node-03'})
            )
    sess.post(
            url_project + 'proj-03' + '/connect_node',
            data=json.dumps({'node': 'node-05'})
            )

    # Assigning networks to projects
    url_network = 'http://127.0.0.1:8000/network/'
    for i in ['net-01', 'net-02', 'net-03']:
        sess.put(
                url_network + i,
                data=json.dumps(
                    {"owner": "proj-01", "access": "proj-01", "net_id": ""}
                    )
                )

    for i in ['net-04', 'net-05']:
        sess.put(
                url_network + i,
                data=json.dumps(
                    {"owner": "proj-02", "access": "proj-02", "net_id": ""}
                    )
                )


# -- SETUP --
@pytest.fixture(scope="module")
def create_setup(request):
    dir_names = make_config()
    initialize_db()
    proc1 = run_server(['haas', 'serve', '8000'])
    proc2 = run_server(['haas', 'serve_networks'])
    time.sleep(1)
    populate_server()
    print("coming from create_setup")

    def fin():
        proc1.terminate()
        proc2.terminate()
        cleanup(dir_names)
        print("tearing down HIL setup")
    request.addfinalizer(fin)


@pytest.mark.usefixtures("create_setup")
class Test_node:
    """ Tests Node related client calls. """

    def test_list_nodes_free(self):
        result = C.node.list('free')
        assert result == [u'node-06', u'node-07', u'node-08', u'node-09']

    def test_list_nodes_all(self):
        result = C.node.list('all')
        assert result == [
                u'node-01', u'node-02', u'node-03', u'node-04', u'node-05',
                u'node-06', u'node-07', u'node-08', u'node-09'
                ]

    def test_show_node(self):
        result = C.node.show('node-07')
        assert result == {
                u'metadata': {},
                u'project': None,
                u'nics': [
                    {
                        u'macaddr': u'aa:bb:cc:dd:ee:07',
                        u'networks': {}, u'label': u'eth0'
                        }
                    ],
                u'name': u'node-07'
                }

    def test_power_cycle(self):
        result = C.node.power_cycle('node-07')
        assert result is None

    def test_power_off(self):
        result = C.node.power_off('node-07')
        assert result is None

    def test_node_add_nic(self):
        C.node.remove_nic('node-08', 'eth0')
        result = C.node.add_nic('node-08', 'eth0', 'aa:bb:cc:dd:ee:ff')
        assert result is None

    def test_node_add_duplicate_nic(self):
        C.node.remove_nic('node-08', 'eth0')
        C.node.add_nic('node-08', 'eth0', 'aa:bb:cc:dd:ee:ff')
        with pytest.raises(Exception):
            C.node.add_nic('node-08', 'eth0', 'aa:bb:cc:dd:ee:ff')

    def test_nosuch_node_add_nic(self):
        with pytest.raises(Exception):
            C.node.add_nic('abcd', 'eth0', 'aa:bb:cc:dd:ee:ff')

    def test_remove_nic(self):
        result = C.node.remove_nic('node-08', 'eth0')
        assert result is None

    def test_remove_duplicate_nic(self):
        C.node.remove_nic('node-08', 'eth0')
        with pytest.raises(Exception):
            C.node.remove_nic('node-08', 'eth0')

    def test_node_connect_network(self):
        result = C.node.connect_network(
                'node-01', 'eth0', 'net-01', 'vlan/native'
                )
        assert result is None

    def test_node_start_console(self):
        result = C.node.start_console('node-01')
        assert result is None

    def test_node_stop_console(self):
        result = C.node.stop_console('node-01')
        assert result is None


# FIXME: I spent some time on this test. Looks like the pytest
# framework kills the network server before it can detach network.
# def test_node_detach_network(self):
# C.node.connect_network('node-04', 'eth0', 'net-04', 'vlan/native')
# result = C.node.detach_network('node-04', 'eth0', 'net-04')
# assert result is None


@pytest.mark.usefixtures("create_setup")
class Test_project:
    """ Tests project related client calls."""

    def test_list_projects(self):
        """ test for getting list of project """
        result = C.project.list()
        assert result == [u'proj-01', u'proj-02', u'proj-03']

    def test_list_nodes_inproject(self):
        """ test for getting list of nodes connected to a project. """
        result01 = C.project.nodes_in('proj-01')
        result02 = C.project.nodes_in('proj-02')
        assert result01 == [u'node-01']
        assert result02 == [u'node-02', u'node-04']

    def test_list_networks_inproject(self):
        """ test for getting list of networks connected to a project. """
        result = C.project.networks_in('proj-01')
        assert result == [u'net-01', u'net-02', u'net-03']

    def test_project_create(self):
        """ test for creating project. """
        result = C.project.create('dummy-01')
        assert result is None

    def test_duplicate_project_create(self):
        """ test for catching duplicate name while creating new project. """
        C.project.create('dummy-02')
        with pytest.raises(Exception):
            C.project.create('dummy-02')

    def test_project_delete(self):
        """ test for deleting project. """
        C.project.create('dummy-03')
        result = C.project.delete('dummy-03')
        assert result is None

    def test_error_project_delete(self):
        """ test to capture error condition in project delete. """
        with pytest.raises(Exception):
            C.project.delete('dummy-03')

    def test_project_connect_node(self):
        """ test for connecting node to project. """
        C.project.create('proj-04')
        result = C.project.connect('proj-04', 'node-06')
        assert result is None

    def test_project_connect_node_duplicate(self):
        """ test for erronous reconnecting node to project. """
        C.project.create('proj-05')
        C.project.connect('proj-05', 'node-07')
        with pytest.raises(Exception):
            C.project.connect('proj-05', 'node-07')

    def test_project_connect_node_nosuchobject(self):
        """ test for connecting no such node or project """
        C.project.create('proj-06')
        with pytest.raises(Exception):
            C.project.connect('proj-06', 'no-such-node')
        with pytest.raises(Exception):
            C.project.connect('no-such-project', 'node-06')

    def test_project_detach_node(self):
        """ Test for correctly detaching node from project."""
        C.project.create('proj-07')
        C.project.connect('proj-07', 'node-08')
        result = C.project.detach('proj-07', 'node-08')
        assert result is None

    def test_project_detach_node_nosuchobject(self):
        """ Test for while detaching node from project."""
        C.project.create('proj-08')
        with pytest.raises(Exception):
            C.project.detach('proj-08', 'no-such-node')
        with pytest.raises(Exception):
            C.project.detach('no-such-project', 'node-06')


@pytest.mark.usefixtures("create_setup")
class Test_switch:
    """ Tests switch related client calls."""

    def test_list_switches(self):
        result = C.switch.list()
        assert result == [u'brocade-01', u'dell-01', u'mock-01', u'nexus-01']

    def test_show_switch(self):
        result = C.switch.show('dell-01')
        assert result == {u'name': u'dell-01', u'ports': []}

    def test_delete_switch(self):
        result = C.switch.delete('nexus-01')
        assert result is None


@pytest.mark.usefixtures("create_setup")
class Test_port:
    """ Tests port related client calls."""

    def test_port_register(self):
        result = C.port.register('mock-01', 'gi1/1/1')
        assert result is None

    def test_port_dupregister(self):
        C.port.register('mock-01', 'gi1/1/2')
        with pytest.raises(Exception):
            C.port.register('mock-01', 'gi1/1/2')

    def test_port_delete(self):
        C.port.register('mock-01', 'gi1/1/3')
        result = C.port.delete('mock-01', 'gi1/1/3')
        assert result is None

    def test_port_delete_error(self):
        C.port.register('mock-01', 'gi1/1/4')
        C.port.delete('mock-01', 'gi1/1/4')
        with pytest.raises(Exception):
            C.port.delete('mock-01', 'gi1/1/4')

    def test_port_connect_nic(self):
        C.port.register('mock-01', 'gi1/1/5')
        result = C.port.connect_nic('mock-01', 'gi1/1/5', 'node-08', 'eth0')
        assert result is None

    def test_port_connect_nic_error(self):
        C.port.register('mock-01', 'gi1/1/6')
        C.port.connect_nic('mock-01', 'gi1/1/6', 'node-09', 'eth0')
        with pytest.raises(Exception):
            C.port.connect_nic('mock-01', 'gi1/1/6', 'node-08', 'eth0')

    def test_port_detach_nic(self):
        C.port.register('mock-01', 'gi1/1/7')
        C.port.connect_nic('mock-01', 'gi1/1/7', 'node-09', 'eth0')
        result = C.port.detach_nic('mock-01', 'gi1/1/7')
        assert result is None

    def test_port_detach_nic_error(self):
        C.port.register('mock-01', 'gi1/1/8')
        with pytest.raises(Exception):
            C.port.detach_nic('mock-01', 'gi1/1/8')


@pytest.mark.usefixtures("create_setup")
class Test_user:
    """ Tests user related client calls."""

    def test_user_create(self):
        """ Test user creation. """
        result1 = C.user.create('billy', 'pass1234', 'admin')
        result2 = C.user.create('bobby', 'pass1234', 'regular')
        assert result1 is None
        assert result2 is None

    def test_user_create_duplicate(self):
        """ Test duplicate user creation. """
        C.user.create('bill', 'pass1234', 'regular')
        with pytest.raises(Exception):
            C.user.create('bill', 'pass1234', 'regular')

    def test_user_delete(self):
        """ Test user deletion. """
        C.user.create('jack', 'pass1234', 'admin')
        result = C.user.delete('jack')
        assert result is None

    def test_user_delete_error(self):
        """ Test error condition in user deletion. """
        C.user.create('Ata', 'pass1234', 'admin')
        C.user.delete('Ata')
        with pytest.raises(Exception):
            C.user.delete('Ata')

    def test_user_add(self):
        """ test adding a user to a project. """
        C.project.create('proj-sample')
        C.user.create('Sam', 'pass1234', 'regular')
        result = C.user.add('Sam', 'proj-sample')
        assert result is None

    def test_user_add_error(self):
        """Test error condition while granting user access to a project."""
        C.project.create('test-proj01')
        C.user.create('sam01', 'pass1234', 'regular')
        C.user.add('sam01', 'test-proj01')
        with pytest.raises(Exception):
            C.user.add('sam01', 'test-proj01')

    def test_user_remove(self):
        """Test revoking user's access to a project. """
        C.project.create('test-proj02')
        C.user.create('sam02', 'pass1234', 'regular')
        C.user.add('sam02', 'test-proj02')
        result = C.user.remove('sam02', 'test-proj02')
        assert result is None

    def test_user_remove_error(self):
        """Test error condition while revoking user access to a project. """
        C.project.create('test-proj03')
        C.user.create('sam03', 'pass1234', 'regular')
        C.user.create('xxxx', 'pass1234', 'regular')
        C.user.add('sam03', 'test-proj03')
        C.user.remove('sam03', 'test-proj03')
        with pytest.raises(Exception):
            C.user.remove('sam03', 'test_proj03')


@pytest.mark.usefixtures("create_setup")
class Test_network:
    """ Tests network related client calls. """

    def test_network_list(self):
        """ Test list of networks. """
        result = C.network.list()
        assert result == {
                u'net-01': {u'network_id': u'1001', u'projects': [u'proj-01']},
                u'net-02': {u'network_id': u'1002', u'projects': [u'proj-01']},
                u'net-03': {u'network_id': u'1003', u'projects': [u'proj-01']},
                u'net-04': {u'network_id': u'1004', u'projects': [u'proj-02']},
                u'net-05': {u'network_id': u'1005', u'projects': [u'proj-02']}
                }

    def test_network_show(self):
        """ Test show network. """
        result = C.network.show('net-01')
        assert result == {
                u'access': [u'proj-01'],
                u'channels': [u'vlan/native', u'vlan/1001'],
                u'name': u'net-01',
                u'owner': u'proj-01'
                }

    def test_network_create(self):
        """ Test create network. """
        result = C.network.create('net-abcd', 'proj-01', 'proj-01', '')
        assert result is None

    def test_network_create_duplicate(self):
        """ Test error condition in create network. """
        C.network.create('net-123', 'proj-01', 'proj-01', '')
        with pytest.raises(Exception):
            C.network.create('net-123', 'proj-01', 'proj-01', '')

    def test_network_delete(self):
        """ Test network deletion """
        C.network.create('net-xyz', 'proj-01', 'proj-01', '')
        result = C.network.delete('net-xyz')
        assert result is None

    def test_network_delete_duplicate(self):
        """ Test error condition in delete network. """
        C.network.create('net-xyz', 'proj-01', 'proj-01', '')
        C.network.delete('net-xyz')
        with pytest.raises(Exception):
            C.network.delete('net-xyz')

    def test_network_grant_project_access(self):
        """ Test granting  a project access to a network. """
        C.network.create('newnet01', 'admin', '', '')
        result1 = C.network.grant_access('proj-02', 'newnet01')
        result2 = C.network.grant_access('proj-03', 'newnet01')
        assert result1 is None
        assert result2 is None

    def test_network_grant_project_access_error(self):
        """ Test error while granting a project access to a network. """
        C.network.create('newnet04', 'admin', '', '')
        C.network.grant_access('proj-02', 'newnet04')
        with pytest.raises(Exception):
            C.network.grant_access('proj-02', 'newnet04')

    def test_network_revoke_project_access(self):
        """ Test revoking a project's access to a network. """
        C.network.create('newnet02', 'admin', '', '')
        C.network.grant_access('proj-02', 'newnet02')
        result = C.network.revoke_access('proj-02', 'newnet02')
        assert result is None

    def test_network_revoke_project_access_error(self):
        """
        Test error condition when revoking project's access to a network.
        """
        C.network.create('newnet03', 'admin', '', '')
        C.network.grant_access('proj-02', 'newnet03')
        C.network.revoke_access('proj-02', 'newnet03')
        with pytest.raises(Exception):
            C.network.revoke_access('proj-02', 'newnet03')


# End of tests ##
