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
from haas.test_common import *
from haas.network_allocator import get_network_allocator
import pytest
import json

import requests
import os
import tempfile
import subprocess
from subprocess import check_call, Popen
from urlparse import urljoin
import requests
from requests.exceptions import ConnectionError
#from haas.client_lib.client_lib import hilClientLib
## Hook to the client library
from haas.client.base import ClientBase
from haas.client.auth import auth_db
from haas.client.client import Client




MOCK_SWITCH_TYPE = 'http://schema.massopencloud.org/haas/v0/switches/mock'
OBM_TYPE_MOCK = 'http://schema.massopencloud.org/haas/v0/obm/mock'
OBM_TYPE_IPMI = 'http://schema.massopencloud.org/haas/v0/obm/ipmi'

ep = "http://127.0.0.1:8888" or os.environ.get('HAAS_ENDPOINT')
username = "hil_user" or os.environ.get('HAAS_USERNAME')
password = "hil_pass1234" or os.environ.get('HAAS_PASSWORD')


auth = auth_db(username, password)

C = Client(ep, auth) #Initializing client library


## Following tests check if the client library is initialized correctly

def test_auth_db():
    auth = auth_db(username, password)
    assert auth.decode('base64', 'strict') == (":").join([username, password])


class Test_ClientBase:
    """ When the username, password is not defined
    It should raise a LookupError
    """

    def test_init_error(self):
        try:
            x = ClientBase()
        except LookupError:
            assert True

    def test_correct_init(self):
        x = ClientBase(ep, 'some_base64_string')
        assert x.endpoint == "http://127.0.0.1:8888"
        assert x.auth == "some_base64_string"

    def test_object_url(self):
        x = ClientBase(ep, 'some_base64_string')
        y = x.object_url('abc', '123', 'xy23z')
        assert y == 'http://127.0.0.1:8888/abc/123/xy23z'

#For testing the client library we need a running HIL server, with dummy
#objects populated. Following classes accomplish that end. 
# It shall:
#       1. Configures haas.cfg
#       2. Instantiates a database
#       3. Starts a server on an arbitary port
#       4. Populates haas with dummy objects
#       5. tears down the setup in a clean fashion.


#pytest.fixture(scope="module")

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
            '[general]'
            'log_level = debug',

            '[auth]',
            'require_authentication = False',

            '[headnode]',
            'base_imgs = base-headnode, img1, img2, img3, img4',
            '[database]',
            'uri = sqlite:///%s/haas.db' % tmpdir,
            '[extensions]',
            'haas.ext.auth.null =',
            'haas.ext.network_allocators.null =',
            '[extensions]',
            'haas.ext.switches.mock =',
            'haas.ext.auth.null =',
            'haas.ext.switches.nexus =',
            'haas.ext.switches.dell =',
            'haas.ext.switches.brocade =',

            'haas.ext.obm.ipmi =',
            'haas.ext.network_allocators.null =',
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


def run_server(cmd):
    """This function starts a haas server.
    The arguments in 'cmd' will be a list of arguments like required to start a
    haas server like ['haas', 'serve', '8888']
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

    ## Adding nodes, node-01 - node-06
    url_node = 'http://127.0.0.1:8888/node/'
    api_nodename='http://schema.massopencloud.org/haas/v0/obm/'

    obminfo1 = {"type": api_nodename+'ipmi', "host":"10.10.0.01",
            "user":"ipmi_u", "password":"pass1234" }

    obminfo2 = {"type": api_nodename+'ipmi', "host":"10.10.0.02",
            "user":"ipmi_u", "password":"pass1234" }

    obminfo3 = {"type": api_nodename+'ipmi', "host":"10.10.0.03",
            "user":"ipmi_u", "password":"pass1234" }

    obminfo4 = {"type": api_nodename+'ipmi', "host":"10.10.0.04",
            "user":"ipmi_u", "password":"pass1234" }


    obminfo5 = {"type": api_nodename+'ipmi', "host":"10.10.0.05",
            "user":"ipmi_u", "password":"pass1234" }

    obminfo6 = {"type": api_nodename+'ipmi', "host":"10.10.0.06",
            "user":"ipmi_u", "password":"pass1234" }


    requests.put(url_node+'node-01', data=json.dumps({"obm":obminfo1}))
    requests.put(url_node+'node-02', data=json.dumps({"obm":obminfo2}))
    requests.put(url_node+'node-03', data=json.dumps({"obm":obminfo3}))
    requests.put(url_node+'node-04', data=json.dumps({"obm":obminfo4}))
    requests.put(url_node+'node-05', data=json.dumps({"obm":obminfo5}))
    requests.put(url_node+'node-06', data=json.dumps({"obm":obminfo6}))

    ## Adding Projects proj-01 - proj-03
    for i in [ "proj-01", "proj-02", "proj-03" ]:
        requests.put('http://127.0.0.1:8888/project/'+i)

    ## Adding switches one for each driver
    url='http://127.0.0.1:8888/switch/'
    api_name='http://schema.massopencloud.org/haas/v0/switches/'

    dell_param={ 'type':api_name+'powerconnect55xx', 'hostname':'dell-01',
            'username':'root', 'password':'root1234' }
    nexus_param={ 'type':api_name+'nexus', 'hostname':'nexus-01',
            'username':'root', 'password':'root1234', 'dummy_vlan':'333' }
    mock_param={ 'type':api_name+'mock', 'hostname':'mockSwitch-01',
            'username':'root', 'password':'root1234' }
    brocade_param={ 'type':api_name+'brocade', 'hostname':'brocade-01',
            'username':'root', 'password':'root1234', 'interface_type':
            'TenGigabitEthernet' }

    requests.put(url+'dell-01', data=json.dumps(dell_param))
    requests.put(url+'nexus-01', data=json.dumps(nexus_param))
    requests.put(url+'mock-01', data=json.dumps(mock_param))
    requests.put(url+'brocade-01', data=json.dumps(brocade_param))

    ## Allocating nodes to projects
    url_project = 'http://127.0.0.1:8888/project/'
    # Adding nodes 1 to proj-01
    requests.post( url_project+'proj-01'+'/connect_node', data=json.dumps({'node':'node-01'}))
    # Adding nodes 2, 4 to proj-02
    requests.post( url_project+'proj-02'+'/connect_node', data=json.dumps({'node':'node-02'}))
    requests.post( url_project+'proj-02'+'/connect_node', data=json.dumps({'node':'node-04'}))
    # Adding node  3, 5 to proj-03
    requests.post( url_project+'proj-03'+'/connect_node', data=json.dumps({'node':'node-03'}))
    requests.post( url_project+'proj-03'+'/connect_node', data=json.dumps({'node':'node-05'}))

    ## Assigning networks to projects
    url_network='http://127.0.0.1:8888/network/'
    for i in [ 'net-01', 'net-02', 'net-03' ]:
        requests.put(url_network+i, data=json.dumps({"creator":"proj-01",
            "access": "proj-01", "net_id": ""}))


        # -- SETUP -- #
@pytest.fixture(scope="session")
def create_setup(request):
    dir_names = make_config()
    initialize_db()
    proc = run_server(['haas', 'serve', '8888' ])
    import time
    time.sleep(0.5)
    populate_server()

    def fin():
        proc.terminate()
        cleanup(dir_names)
    request.addfinalizer(fin)





@pytest.mark.usefixtures("create_setup")
class Test_Node:
    """ Tests Node related client calls. """

    def test_list_nodes_free(self):
        result = C.node.list('free')
        assert result == [u'node-06']

    def test_list_nodes_all(self):
        result = C.node.list('all')
        assert result == [u'node-01', u'node-02', u'node-03', u'node-04',
                            u'node-05', u'node-06']


@pytest.mark.usefixtures("create_setup")
class Test_project:
    """ Tests project related client calls."""

    def test_list_projects(self):
        result = C.project.list()
        assert result == [u'proj-01', u'proj-02', u'proj-03']

    def test_list_nodes_inproject(self):
        result01 = C.project.nodes_in('proj-01')
        result02 = C.project.nodes_in('proj-02')
        assert result01 == [u'node-01']
        assert result02 == [u'node-02', u'node-04']

    def test_list_networks_inproject(self):
        result = C.project.networks_in('proj-01')
        assert result == [u'net-01', u'net-02', u'net-03']

@pytest.mark.usefixtures("create_setup")
class Test_switch:
    """ Tests switch related client calls."""

    def test_list_switches(self):
        result = C.switch.list()
        assert result == [u'brocade-01', u'dell-01', u'mock-01', u'nexus-01']

## End of tests ##

