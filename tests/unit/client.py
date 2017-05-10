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
from flask.ext.sqlalchemy import SQLAlchemy
from haas.flaskapp import app
from haas.model import NetworkingAction
from haas.client.base import ClientBase, FailedAPICallException
from haas.client.client import Client, RequestsHTTPClient, KeystoneHTTPClient

import errno
import json
import os
import pytest
import requests
import socket
import subprocess
import tempfile
import time

from subprocess import check_call, Popen
from urlparse import urljoin
import requests
from requests.exceptions import ConnectionError

ep = "http://127.0.0.1:8000" or os.environ.get('HAAS_ENDPOINT')
username = "hil_user" or os.environ.get('HAAS_USERNAME')
password = "hil_pass1234" or os.environ.get('HAAS_PASSWORD')

http_client = RequestsHTTPClient()
http_client.auth = (username, password)
C = Client(ep, http_client)  # Initializing client library
MOCK_SWITCH_TYPE = 'http://schema.massopencloud.org/haas/v0/switches/mock'
OBM_TYPE_MOCK = 'http://schema.massopencloud.org/haas/v0/obm/mock'
OBM_TYPE_IPMI = 'http://schema.massopencloud.org/haas/v0/obm/ipmi'


class Test_ClientBase:
    """Tests client initialization and object_url creation. """

    def test_init_error(self):
        with pytest.raises(TypeError):
            x = ClientBase()

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

db_dir = None


def make_config():
    """ This function creates haas.cfg with desired options
    and writes to a temporary directory.
    It returns a tuple where (tmpdir, cwd) = ('location of haas.cfg', 'pwd')
    """
    tmpdir = tempfile.mkdtemp()
    global db_dir
    db_dir = tmpdir
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


# Allocating nodes to projects
def assign_nodes2project(sess, project, *nodes):
    """ Assigns multiple <nodes> to a <project>.

     Takes as input
     <sess>: session object for REST call, <project>: project name,
     <*nodes> one or more node names.
    """
    url_project = 'http://127.0.0.1:8000/project/'

    for node in nodes:
        sess.post(
                url_project + project + '/connect_node',
                data=json.dumps({'node': node})
        )


def populate_server():
    """
    Once the server is started, this function will populate some mock objects
    to faciliate testing of the client library
    """
    sess = requests.Session()
    sess.auth = (username, password)

    # Adding nodes, node-01 - node-09
    url_node = 'http://127.0.0.1:8000/node/'
    ipmi = 'http://schema.massopencloud.org/haas/v0/obm/ipmi'

    for i in range(1, 10):
        obminfo = {
                "type": ipmi, "host": "10.10.0.0"+repr(i),
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
    assign_nodes2project(sess, 'proj-01', 'node-01')
    assign_nodes2project(sess, 'proj-02', 'node-02', 'node-04')
    assign_nodes2project(sess, 'proj-03', 'node-03', 'node-05')

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


class TimeoutError(Exception):
    pass


# FIX ME: Replace this function with show_networking_action call, once it
# gets implemented.
def avoid_network_race_condition():
    """Checks for networking actions queue to be empty.

    Used to avoid race condition between subsequent network calls
    on the same object.
    """
    global db_dir
    uri = 'sqlite:///'+db_dir+'/haas.db'
    db = SQLAlchemy(app)
    app.config.update(SQLALCHEMY_DATABASE_URI=uri)

    for timeout in range(10):
        que = db.session.query(NetworkingAction).count()
        if (que > 0):
            time.sleep(1)
        else:
            return
    raise TimeoutError(" Timed out to avoid race condition. ")


@pytest.fixture(scope="module")
def create_setup(request):
    serv_port = 8000
    SERVER_TIMEOUT_SECS = 60

    dir_names = make_config()
    initialize_db()
    proc1 = Popen(['haas', 'serve', str(serv_port)])
    proc2 = Popen(['haas', 'serve_networks'])

    # Loop until the server is up. See #770
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    begin = time.time()
    while True:
        try:
            sock.connect(('127.0.0.1', serv_port))
            break
        except socket.error as serr:
            if serr.errno == errno.ECONNREFUSED:
                if (time.time() - begin) < SERVER_TIMEOUT_SECS:
                    time.sleep(1)
                else:
                    raise TimeoutError("Client library test server didn't " +
                            "start in {} seconds".format(SERVER_TIMEOUT_SECS))
            else:
                raise serr
        finally:
            sock.close()

    populate_server()

    def fin():
        proc1.terminate()
        proc2.terminate()
        proc1.wait()
        proc2.wait()
        cleanup(dir_names)
    request.addfinalizer(fin)


@pytest.mark.usefixtures("create_setup")
class Test_node:
    """ Tests Node related client calls. """

    def test_list_nodes_free(self):
        assert C.node.list('free') == [
                u'node-06', u'node-07', u'node-08', u'node-09'
                ]

    def test_list_nodes_all(self):
        assert C.node.list('all') == [
                u'node-01', u'node-02', u'node-03', u'node-04', u'node-05',
                u'node-06', u'node-07', u'node-08', u'node-09'
                ]

    def test_show_node(self):
        assert C.node.show('node-07') == {
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
        assert C.node.power_cycle('node-07') is None

    def test_power_off(self):
        assert C.node.power_off('node-07') is None

    def test_node_add_nic(self):
        C.node.remove_nic('node-08', 'eth0')
        assert C.node.add_nic('node-08', 'eth0', 'aa:bb:cc:dd:ee:ff') is None

    def test_node_add_duplicate_nic(self):
        C.node.remove_nic('node-08', 'eth0')
        C.node.add_nic('node-08', 'eth0', 'aa:bb:cc:dd:ee:ff')
        with pytest.raises(FailedAPICallException):
            C.node.add_nic('node-08', 'eth0', 'aa:bb:cc:dd:ee:ff')

    def test_nosuch_node_add_nic(self):
        with pytest.raises(FailedAPICallException):
            C.node.add_nic('abcd', 'eth0', 'aa:bb:cc:dd:ee:ff')

    def test_remove_nic(self):
        assert C.node.remove_nic('node-08', 'eth0') is None

    def test_remove_duplicate_nic(self):
        C.node.remove_nic('node-08', 'eth0')
        with pytest.raises(FailedAPICallException):
            C.node.remove_nic('node-08', 'eth0')

    def test_node_start_console(self):
        assert C.node.start_console('node-01') is None

    def test_node_stop_console(self):
        assert C.node.stop_console('node-01') is None

    def test_node_connect_network(self):
        assert C.node.connect_network(
                'node-01', 'eth0', 'net-01', 'vlan/native'
                ) is None

    def test_node_connect_network_error(self):
        C.node.connect_network('node-02', 'eth0', 'net-04', 'vlan/native')
        with pytest.raises(FailedAPICallException):
            C.node.connect_network('node-02', 'eth0', 'net-04', 'vlan/native')

    def test_node_detach_network(self):
        C.node.connect_network('node-04', 'eth0', 'net-04', 'vlan/native')
        avoid_network_race_condition()
        assert C.node.detach_network('node-04', 'eth0', 'net-04') is None

    def test_node_detach_network_error(self):
        C.node.connect_network('node-04', 'eth0', 'net-04', 'vlan/native')
        avoid_network_race_condition()
        C.node.detach_network('node-04', 'eth0', 'net-04')
        with pytest.raises(FailedAPICallException):
            C.node.detach_network('node-04', 'eth0', 'net-04')


@pytest.mark.usefixtures("create_setup")
class Test_project:
    """ Tests project related client calls."""

    def test_list_projects(self):
        """ test for getting list of project """
        assert C.project.list() == [u'proj-01', u'proj-02', u'proj-03']

    def test_list_nodes_inproject(self):
        """ test for getting list of nodes connected to a project. """
        assert C.project.nodes_in('proj-01') == [u'node-01']
        assert C.project.nodes_in('proj-02') == [u'node-02', u'node-04']

    def test_list_networks_inproject(self):
        """ test for getting list of networks connected to a project. """
        assert C.project.networks_in('proj-01') == [
                u'net-01', u'net-02', u'net-03'
                ]

    def test_project_create(self):
        """ test for creating project. """
        assert C.project.create('dummy-01') is None

    def test_duplicate_project_create(self):
        """ test for catching duplicate name while creating new project. """
        C.project.create('dummy-02')
        with pytest.raises(FailedAPICallException):
            C.project.create('dummy-02')

    def test_project_delete(self):
        """ test for deleting project. """
        C.project.create('dummy-03')
        assert C.project.delete('dummy-03') is None

    def test_error_project_delete(self):
        """ test to capture error condition in project delete. """
        with pytest.raises(FailedAPICallException):
            C.project.delete('dummy-03')

    def test_project_connect_node(self):
        """ test for connecting node to project. """
        C.project.create('proj-04')
        assert C.project.connect('proj-04', 'node-06') is None

    def test_project_connect_node_duplicate(self):
        """ test for erronous reconnecting node to project. """
        C.project.create('proj-05')
        C.project.connect('proj-05', 'node-07')
        with pytest.raises(FailedAPICallException):
            C.project.connect('proj-05', 'node-07')

    def test_project_connect_node_nosuchobject(self):
        """ test for connecting no such node or project """
        C.project.create('proj-06')
        with pytest.raises(FailedAPICallException):
            C.project.connect('proj-06', 'no-such-node')
        with pytest.raises(FailedAPICallException):
            C.project.connect('no-such-project', 'node-06')

    def test_project_detach_node(self):
        """ Test for correctly detaching node from project."""
        C.project.create('proj-07')
        C.project.connect('proj-07', 'node-08')
        assert C.project.detach('proj-07', 'node-08') is None

    def test_project_detach_node_nosuchobject(self):
        """ Test for while detaching node from project."""
        C.project.create('proj-08')
        with pytest.raises(FailedAPICallException):
            C.project.detach('proj-08', 'no-such-node')
        with pytest.raises(FailedAPICallException):
            C.project.detach('no-such-project', 'node-06')


@pytest.mark.usefixtures("create_setup")
class Test_switch:
    """ Tests switch related client calls."""

    def test_list_switches(self):
        assert C.switch.list() == [
                u'brocade-01', u'dell-01', u'mock-01', u'nexus-01'
                ]

    def test_show_switch(self):
        assert C.switch.show('dell-01') == {u'name': u'dell-01', u'ports': []}

    def test_delete_switch(self):
        assert C.switch.delete('nexus-01') is None


@pytest.mark.usefixtures("create_setup")
class Test_port:
    """ Tests port related client calls."""

    def test_port_register(self):
        assert C.port.register('mock-01', 'gi1/1/1') is None

    def test_port_dupregister(self):
        C.port.register('mock-01', 'gi1/1/2')
        with pytest.raises(FailedAPICallException):
            C.port.register('mock-01', 'gi1/1/2')

    def test_port_delete(self):
        C.port.register('mock-01', 'gi1/1/3')
        assert C.port.delete('mock-01', 'gi1/1/3') is None

    def test_port_delete_error(self):
        C.port.register('mock-01', 'gi1/1/4')
        C.port.delete('mock-01', 'gi1/1/4')
        with pytest.raises(FailedAPICallException):
            C.port.delete('mock-01', 'gi1/1/4')

    def test_port_connect_nic(self):
        C.port.register('mock-01', 'gi1/1/5')
        assert C.port.connect_nic(
                'mock-01', 'gi1/1/5', 'node-08', 'eth0'
                ) is None

    def test_port_connect_nic_error(self):
        C.port.register('mock-01', 'gi1/1/6')
        C.port.connect_nic('mock-01', 'gi1/1/6', 'node-09', 'eth0')
        with pytest.raises(FailedAPICallException):
            C.port.connect_nic('mock-01', 'gi1/1/6', 'node-08', 'eth0')

    def test_port_detach_nic(self):
        C.port.register('mock-01', 'gi1/1/7')
        C.port.connect_nic('mock-01', 'gi1/1/7', 'node-09', 'eth0')
        assert C.port.detach_nic('mock-01', 'gi1/1/7') is None

    def test_port_detach_nic_error(self):
        C.port.register('mock-01', 'gi1/1/8')
        with pytest.raises(FailedAPICallException):
            C.port.detach_nic('mock-01', 'gi1/1/8')


@pytest.mark.usefixtures("create_setup")
class Test_user:
    """ Tests user related client calls."""

    def test_user_create(self):
        """ Test user creation. """
        assert C.user.create('billy', 'pass1234', 'admin') is None
        assert C.user.create('bobby', 'pass1234', 'regular') is None

    def test_user_create_duplicate(self):
        """ Test duplicate user creation. """
        C.user.create('bill', 'pass1234', 'regular')
        with pytest.raises(FailedAPICallException):
            C.user.create('bill', 'pass1234', 'regular')

    def test_user_delete(self):
        """ Test user deletion. """
        C.user.create('jack', 'pass1234', 'admin')
        assert C.user.delete('jack') is None

    def test_user_delete_error(self):
        """ Test error condition in user deletion. """
        C.user.create('Ata', 'pass1234', 'admin')
        C.user.delete('Ata')
        with pytest.raises(FailedAPICallException):
            C.user.delete('Ata')

    def test_user_add(self):
        """ test adding a user to a project. """
        C.project.create('proj-sample')
        C.user.create('Sam', 'pass1234', 'regular')
        assert C.user.add('Sam', 'proj-sample') is None

    def test_user_add_error(self):
        """Test error condition while granting user access to a project."""
        C.project.create('test-proj01')
        C.user.create('sam01', 'pass1234', 'regular')
        C.user.add('sam01', 'test-proj01')
        with pytest.raises(FailedAPICallException):
            C.user.add('sam01', 'test-proj01')

    def test_user_remove(self):
        """Test revoking user's access to a project. """
        C.project.create('test-proj02')
        C.user.create('sam02', 'pass1234', 'regular')
        C.user.add('sam02', 'test-proj02')
        assert C.user.remove('sam02', 'test-proj02') is None

    def test_user_remove_error(self):
        """Test error condition while revoking user access to a project. """
        C.project.create('test-proj03')
        C.user.create('sam03', 'pass1234', 'regular')
        C.user.create('xxxx', 'pass1234', 'regular')
        C.user.add('sam03', 'test-proj03')
        C.user.remove('sam03', 'test-proj03')
        with pytest.raises(FailedAPICallException):
            C.user.remove('sam03', 'test_proj03')


@pytest.mark.usefixtures("create_setup")
class Test_network:
    """ Tests network related client calls. """

    def test_network_list(self):
        """ Test list of networks. """
        assert C.network.list() == {
                u'net-01': {u'network_id': u'1001', u'projects': [u'proj-01']},
                u'net-02': {u'network_id': u'1002', u'projects': [u'proj-01']},
                u'net-03': {u'network_id': u'1003', u'projects': [u'proj-01']},
                u'net-04': {u'network_id': u'1004', u'projects': [u'proj-02']},
                u'net-05': {u'network_id': u'1005', u'projects': [u'proj-02']}
                }

    def test_network_show(self):
        """ Test show network. """
        assert C.network.show('net-01') == {
                u'access': [u'proj-01'],
                u'channels': [u'vlan/native', u'vlan/1001'],
                u'name': u'net-01',
                u'owner': u'proj-01'
                }

    def test_network_create(self):
        """ Test create network. """
        assert C.network.create('net-abcd', 'proj-01', 'proj-01', '') is None

    def test_network_create_duplicate(self):
        """ Test error condition in create network. """
        C.network.create('net-123', 'proj-01', 'proj-01', '')
        with pytest.raises(FailedAPICallException):
            C.network.create('net-123', 'proj-01', 'proj-01', '')

    def test_network_delete(self):
        """ Test network deletion """
        C.network.create('net-xyz', 'proj-01', 'proj-01', '')
        assert C.network.delete('net-xyz') is None

    def test_network_delete_duplicate(self):
        """ Test error condition in delete network. """
        C.network.create('net-xyz', 'proj-01', 'proj-01', '')
        C.network.delete('net-xyz')
        with pytest.raises(FailedAPICallException):
            C.network.delete('net-xyz')

    def test_network_grant_project_access(self):
        """ Test granting  a project access to a network. """
        C.network.create('newnet01', 'admin', '', '')
        assert C.network.grant_access('proj-02', 'newnet01') is None
        assert C.network.grant_access('proj-03', 'newnet01') is None

    def test_network_grant_project_access_error(self):
        """ Test error while granting a project access to a network. """
        C.network.create('newnet04', 'admin', '', '')
        C.network.grant_access('proj-02', 'newnet04')
        with pytest.raises(FailedAPICallException):
            C.network.grant_access('proj-02', 'newnet04')

    def test_network_revoke_project_access(self):
        """ Test revoking a project's access to a network. """
        C.network.create('newnet02', 'admin', '', '')
        C.network.grant_access('proj-02', 'newnet02')
        assert C.network.revoke_access('proj-02', 'newnet02') is None

    def test_network_revoke_project_access_error(self):
        """
        Test error condition when revoking project's access to a network.
        """
        C.network.create('newnet03', 'admin', '', '')
        C.network.grant_access('proj-02', 'newnet03')
        C.network.revoke_access('proj-02', 'newnet03')
        with pytest.raises(FailedAPICallException):
            C.network.revoke_access('proj-02', 'newnet03')
