"""Unit tests for api.py"""
import haas
from haas import model, api, deferred, server, config
from haas.test_common import *
from haas.rest import RequestContext
import pytest
import json


MOCK_SWITCH_TYPE = 'http://schema.massopencloud.org/haas/v0/switches/mock'
OBM_TYPE_MOCK = 'http://schema.massopencloud.org/haas/v0/obm/mock'
OBM_TYPE_IPMI = 'http://schema.massopencloud.org/haas/v0/obm/ipmi'


@pytest.fixture
def configure():
    config_testsuite()
    config_merge({
        'extensions': {
            'haas.ext.switches.mock': '',
            'haas.ext.obm.ipmi': '',
            'haas.ext.obm.mock': '',
        },
    })
    config.load_extensions()


@pytest.fixture
def db(request):
    return fresh_database(request)


@pytest.fixture
def server_init():
    server.register_drivers()
    server.validate_state()


@pytest.yield_fixture
def with_request_context():
    with RequestContext():
        yield


pytestmark = pytest.mark.usefixtures('configure',
                                     'db',
                                     'server_init',
                                     'with_request_context')




class TestRegisterCorrectObm:
    """Tests that node_register stores obm driver information into 
    correct corresponding tables
    """
    def test_ipmi(self, db):
	api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
                  "host": "ipmihost",
                  "user": "root",
                  "password": "tapeworm"})

	node_obj = db.query(model.Node).filter_by(label="compute-01")\
			.join(model.Obm).join(haas.ext.obm.ipmi.Ipmi).first()

	
	assert str(node_obj.label) == 'compute-01'		#Comes from table node
	assert str(node_obj.obm.api_name) == OBM_TYPE_IPMI	#Comes from table obm
	assert str(node_obj.obm.host) == 'ipmihost'		#Comes from table ipmi


    def test_mockobm(self, db):
        api.node_register('compute-01', obm={
                  "type": "http://schema.massopencloud.org/haas/v0/obm/mock",
                  "host": "mockObmhost",
                  "user": "root",
                  "password": "tapeworm"})

        node_obj = db.query(model.Node).filter_by(label="compute-01")\
                        .join(model.Obm).join(haas.ext.obm.mock.MockObm).first()

	assert str(node_obj.label) == 'compute-01'		#Comes from table node
	assert str(node_obj.obm.api_name) == OBM_TYPE_MOCK 	#Comes from table obm
	assert str(node_obj.obm.host) == 'mockObmhost'		#Comes from table mockobm

