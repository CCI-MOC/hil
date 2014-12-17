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

"""A switch driver that maintains local state only.

Useful for testing switch drivers such as the simple and complex VLAN drivers.
This driver will probably not work correctly outside of the testing
environment.

If there are two switches in the config that have the same name, their changes
will clash with each other.

Before using this switch driver in a test, make sure to call the
'reinitialize' function, to erase any existing local state.
"""

# This dictionary holds all of the port statuses for all instantiations of the driver.
LOCAL_STATE = {}

def reinitialize():
    """Erase all local state.

    When using this driver in the test suite, call this function at the
    beginning of every test, to make sure that tests don't influence each
    other.
    """

    global LOCAL_STATE
    LOCAL_STATE = {}

def apply_networking(net_map, config):

    global LOCAL_STATE

    if config["name"] not in LOCAL_STATE:
        LOCAL_STATE[config["name"]] = {}

    for port in net_map:
        LOCAL_STATE[config["name"]][port] = net_map[port]


def get_switch_vlans(config, vlan_list):

    vlan_cfgs = {}

    for vlan in vlan_list:
        vlan_cfgs[vlan] = []

    for port in LOCAL_STATE[config["name"]]:
        vlan = LOCAL_STATE[config["name"]][port]
        if vlan is not None:
            vlan_cfgs[vlan].append(port)

    return vlan_cfgs
