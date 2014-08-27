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
import json

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
        # Use the deployment config for these tests.  Setup such as the switch
        # IP address and password must be in this file, as well as the allowed
        # VLAN range.
        # XXX: Currently, the deployment tests only support the Dell driver.
        cfg.read('deployment.cfg')
 
    def allocate_nodes():
        arch_json_file = cfg.get('deployment tests', 'site_layout_json')
        arch_json_data = open(arch_json_file)
        arch = json.load(arch_json_data)
        arch_json_data.close()

        api.switch_register(arch['switch'], arch['driver'])

        for node in arch['nodes']:
            api.node_register(node['name'], node['ipmi']['host'], 
                node['ipmi']['user'], node['ipmi']['pass'])
            for nic in node['nics']:
                api.node_register_nic(node['name'], nic['name'], nic['mac'])
                api.port_register(arch['switch'], nic['port'])
                api.port_connect_nic(
                    arch['switch'], nic['port'], 
                    node['name'], nic['name'])

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
    """A decorator which cleans up headnode VMs left by tests.  This is to
    work around an irritating bug in some versions of libvirt, which causes
    'virsh undefine' to fail if called too quickly.  This decorator depends on
    the database containing an accurate list of headnodes.
    """

    def undefine_headnodes(db):
        trunk_nic = cfg.get('headnode', 'trunk_nic')
        for hn in db.query(Headnode):
            # XXX: Our current version of libvirt has a bug that causes this 
            # command to hang for a minute and throw an error before 
            # completing successfully.  For this reason, we are ignoring any 
            # errors thrown by 'virsh undefine'. This should be changed once 
            # we start using a version of libvirt that has fixed this bug.
            call(['virsh', 'undefine', hn._vmname(), '--remove-all-storage'])

    @wraps(f)
    def wrapped(self, db):
        try:
            f(self, db)
        finally:
            undefine_headnodes(db)

    return wrapped

