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

from haas.model import *
from haas.config import cfg
from haas import api, config
import json
import subprocess
import os.path


def testsuite_config():
    """A pytest fixture which loads an initial config from ``testsuite.cfg``.

    Tests which don't care about a specific configuration should leave the
    config alone. This allows the developer to test with different
    configurations, e.g. different DBMS backends.

    if testsuite.cfg doesn't exist, sane defaults are provided.
    """
    # NOTE: The file ``testsuite.cfg.default`` Should be updated whenever
    # The default settings here are modified.
    if os.path.isfile('testsuite.cfg'):
        config.load('testsuite.cfg')
    else:
        config_set({
            'general': {
                # TODO: this is going away soon, but there are still a few
                # parts of the code that use it.
                'driver': 'null',
            },
            'extensions': {
                # Use the null network allocator for these tests
                'haas.ext.network_allocators.null': '',
            },
            'devel': {
                'dry_run': True,
            },
            'headnode': {
                'base_imgs': 'base-headnode, img1, img2, img3, img4',
            },
            'database': {
                'uri': 'sqlite:///:memory:',
            }
        })


def config_merge(config_dict):
    """Modify the configuration according to ``config_dict``.

    ``config_dict`` should be a dictionary mapping section names (strings)
    to dictionaries mapping option names within a section (again, strings)
    to their values. If the value of a section, or option is None, that
    section or option is removed. Otherwise, the section is created if it
    does not exist, and any options are set to the specified values.
    """
    for section in config_dict.keys():
        if config_dict[section] is None:
            print('remove section: %r' % section)
            cfg.remove_section(section)
        else:
            if not cfg.has_section(section):
                print('add section: %r' % section)
                cfg.add_section(section)
            for option in config_dict[section].keys():
                if config_dict[section][option] is None:
                    print('remove option: %r' % option)
                    cfg.remove_option(section, option)
                else:
                    print('set option: %r' % option)
                    cfg.set(section, option, config_dict[section][option])


def config_set(config_dict):
    """Set the configuration according to ``config_dict``.

    This works like ``config_merge``, except that it starts from an empty
    configuration.
    """
    config_clear()
    config_merge(config_dict)


def config_clear():
    """Clear the contents of the current HaaS configuration"""
    for section in cfg.sections():
        cfg.remove_section(section)


def network_create_simple(network, project):
    """Create a simple project-owned network.

    This is a shorthand for the network_create API call, that defaults
    parameters to the most common case---namely, that the network is owned by
    a project, has access only by that project, and uses an allocated
    underlying net_id.  Note that this is the only valid set of parameters for
    a network that belongs to a project.

    The test-suite uses this extensively, for tests that don't care about more
    complicated features of networks.
    """
    api.network_create(network, project, project, "")

def newDB():
    """Configures and returns a connection to a freshly initialized DB."""
    init_db(create=True)
    return Session()

def releaseDB(db):
    """Do we need to do anything here to release resources?"""
    pass


def fresh_database(request):
    """A pytest fixture which runs the test against a newly populated DB.

    This must run *after* the config file (or equivalent) has been loaded.
    """
    db = newDB()
    request.addfinalizer(lambda: releaseDB(db))
    return db


def deployment_test():
    """A which runs the given function on a fresh memory-backed
    database and a config that is setup to operate with a dell switch.  Used
    for testing functions that pertain to the state of the outside world.
    These tests are very specific to our setup and are used for internal
    testing purposes. These tests are unlikely to work with other HaaS
    configurations.
    """
    # Use the deployment config for these tests.  Setup such as the switch
    # IP address and password must be in this file, as well as the allowed
    # VLAN range.
    cfg.read('deployment.cfg')

    def allocate_nodes():
        layout_json_data = open('site-layout.json')
        layout = json.load(layout_json_data)
        layout_json_data.close()

        netmap = {}
        for node in layout['nodes']:
            api.node_register(node['name'], node['ipmi']['host'],
                node['ipmi']['user'], node['ipmi']['pass'])
            for nic in node['nics']:
                api.node_register_nic(node['name'], nic['name'], nic['mac'])
                api.port_register(nic['port'])
                api.port_connect_nic(nic['port'], node['name'], nic['name'])
                netmap[nic['port']] = None

        # Now ensure that all of these ports are turned off
        driver_name = cfg.get('general', 'driver')
        driver = importlib.import_module('haas.drivers.' + driver_name)
        driver.apply_networking(netmap)


def headnode_cleanup(request):
    """A pytest fixture which cleans up headnode VMs left by tests.  This is to
    work around an irritating bug in some versions of libvirt, which causes
    'virsh undefine' to fail if called too quickly.  This decorator depends on
    the database containing an accurate list of headnodes.
    """

    def undefine_headnodes(db):
        for hn in db.query(Headnode):
            # XXX: Our current version of libvirt has a bug that causes this
            # command to hang for a minute and throw an error before
            # completing successfully.  For this reason, we are ignoring any
            # errors thrown by 'virsh undefine'. This should be changed once
            # we start using a version of libvirt that has fixed this bug.
            try:
                hn.delete()
            except subprocess.CalledProcessError:
                pass

    request.addfinalizer(undefine_headnodes)
