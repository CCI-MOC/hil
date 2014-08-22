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

from functools import wraps
from haas.model import *
from haas.config import cfg
from haas import api

def newDB():
    """Configures and returns an in-memory DB connection"""
    init_db(create=True,uri="sqlite:///:memory:")
    return Session()

def releaseDB(db):
    """Do we need to do anything here to release resources?"""
    pass


def clear_configuration(f):
    """A decorator which clears all HaaS configuration both before and after
    calling the function.  Used for tests which require a specific
    configuration setup.
    """

    def config_clear():
        for section in cfg.sections():
            cfg.remove_section(section)

    @wraps(f)
    def wrapped(self):
        config_clear()
        f(self)
        config_clear()

    return wrapped


def database_only(f):
    """A decorator which runs the given function on a fresh memory-backed
    database, and a config that is empty except for making the 'null' backend
    active,  and enabling the dry_run option.  Used for testing functions that
    pertain to the database state, but not the state of the outside world, or
    the network driver.
    """

    def config_initialize():
        # Use the 'null' backend for these tests
        cfg.add_section('general')
        cfg.set('general', 'active_switch', 'null')
        cfg.add_section('devel')
        cfg.set('devel', 'dry_run', True)

    @wraps(f)
    @clear_configuration
    def wrapped(self):
        config_initialize()
        db = newDB()
        f(self, db)
        releaseDB(db)

    return wrapped


def deployment_test(f):
    """A decorator which runs the given function on a fresh memory-backed
    database and a config that is setup to operate with a dell switch.  Used
    for testing functions that pertain to the state of the outside world.
    These tests are very specific to our setup and are used for internal
    testing purposes. These tests are unlikely to work with other HaaS 
    configurations.
    """

    def config_initialize():
        # Use the 'dell' backend for these tests
        cfg.read('deployment.cfg')
 
    def allocate_nodes():
        api.switch_register('dell', 'dell')

        for n in range(4):
            node = n + 195
            ipmi_port = n + 45
            nic1_port = n + 15
            nic2_port = n + 20
            ipmi = 'node-%d-ipmi' % node
            nic1 = 'node-%d-nic1' % node
            nic2 = 'node-%d-nic2' % node
            api.node_register(node)
            api.node_register_nic(node, ipmi, 'FillThisInLater')
            api.node_register_nic(node, nic1, 'FillThisInLater')  
            api.node_register_nic(node, nic2, 'FillThisInLater')
            api.port_register('dell', ipmi_port)
            api.port_register('dell', nic1_port)
            api.port_register('dell', nic2_port)
            api.port_connect_nic('dell', ipmi_port, node, ipmi)
            api.port_connect_nic('dell', nic1_port, node, nic1)
            api.port_connect_nic('dell', nic2_port, node, nic2)

    @wraps(f)
    @clear_configuration
    def wrapped(self):
        config_initialize()
        db = newDB()
        allocate_nodes()
        f(self, db)
        releaseDB(db)

    return wrapped

def headnode_cleanup(f):
    """A decorator which cleans up any vlans and network bridges after a VM
    has been shutdown.  This is intended for deployment tests that do not
    clean up after themselves.  This decorator depends on the database
    containing an accurate list of headnodes and hnics.
    """

    def remove_bridges_and_vlans(db):
        trunk_nic = cfg.get('headnode', 'trunk_nic')
        for hn in db.query(Headnode):
            call(['virsh', 'undefine', hn._vmname(), '--remove-all-storage'])

    @wraps(f)
    def wrapped(self, db):
        try:
            f(self, db)
        finally:
            remove_bridges_and_vlans(db)

    return wrapped

