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

"""Unit tests for api.py"""
import haas
from haas import model, api, deferred, server, config
from haas.model import db
from haas.test_common import *
from haas.network_allocator import get_network_allocator
import pytest
import json

import requests
import os
import subprocess
from urlparse import urljoin
from requests.exceptions import ConnectionError
#from haas.client_lib.client_lib import hilClientLib
## Hook to the client library
from haas.client.base import ClientBase
from haas.client.auth import *
from haas.client.client import Client



MOCK_SWITCH_TYPE = 'http://schema.massopencloud.org/haas/v0/switches/mock'
OBM_TYPE_MOCK = 'http://schema.massopencloud.org/haas/v0/obm/mock'
OBM_TYPE_IPMI = 'http://schema.massopencloud.org/haas/v0/obm/ipmi'

ep = "http://127.0.0.1" or os.environ.get('HAAS_ENDPOINT')
username = "hil_user" or os.environ.get('HAAS_USERNAME')
password = "hil_pass1234" or os.environ.get('HAAS_PASSWORD')


auth = auth_db(username, password)

C = Client(ep, auth) #Initializing client library


@pytest.fixture
def configure():
    config_testsuite()
    config_merge({
        'extensions': {
            'haas.ext.auth.mock'  : '',
# This extension is enabled by default in the tests, so we need to
# disable it explicitly:
            'haas.ext.auth.null': None,
            'haas.ext.switches.mock': '',
            'haas.ext.obm.ipmi': '',
            'haas.ext.obm.mock': '',
        },
    })
    config.load_extensions()


fresh_database = pytest.fixture(fresh_database)


@pytest.fixture
def server_init():
    server.register_drivers()
    server.validate_state()


with_request_context = pytest.yield_fixture(with_request_context)


pytestmark = pytest.mark.usefixtures('configure',
                                     'fresh_database',
                                     'server_init',
                                     'with_request_context')


def test_auth_db():
    auth = auth_db(username, password)
    assert auth.decode('base64', 'strict') == (":").join([username, password])


def test_init_error():
    try:
        x = ClientBase()
    except LookupError:
        assert True


def test_correct_init():
    x = ClientBase(ep, 'some_base64_string')
    assert x.endpoint == "http://127.0.0.1"
    assert x.auth == "some_base64_string"

def test_object_url():
    x = ClientBase(ep, 'some_base64_string')
    y = x.object_url('abc', '123', 'xy23z')
    assert y == 'http://127.0.0.1/abc/123/xy23z'



#class TestNodeOperations:
#    """Tests for the haas.client.node.* operations. """
#
#    def test_list_free_nodes(self):
#        api.node_register('master-control-program', obm={
#            "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
#            "host": "ipmihost",
#            "user": "root",
#            "password": "tapeworm"})
#        api.node_register('robocop', obm={
#            "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
#            "host": "ipmihost",
#            "user": "root",
#            "password": "tapeworm"})
#        api.node_register('data', obm={
#            "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
#            "host": "ipmihost",
#            "user": "root",
#            "password": "tapeworm"})

