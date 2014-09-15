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

"""A driver for VLAN-based setups using a single switch (possibly stacked)

See the documentation for the haas.drivers package for a description of this
module's interface.

An example config:

[general]
driver = simple_vlan

[driver simple_vlan]
switch = {"switch": "dell", "ip": "192.168.0.2", "user": "foo", "pass": "bar"}

"""

import json
import importlib
from haas.config import cfg

# We are a VLAN-based driver with simple allocation
from haas.drivers.driver_tools.vlan import *

def apply_networking(net_map):
    config = json.loads(cfg.get('driver simple_vlan', 'switch'))
    driver = importlib.import_module('haas.drivers.switches.' + config["switch"])
    driver.apply_networking(net_map, config)

def get_switch_vlans(vlan_list):
    config = json.loads(cfg.get('driver simple_vlan', 'switch'))
    driver = importlib.import_module('haas.drivers.switches.' + config['switch'])
    returnee = driver.get_switch_vlans(config, vlan_list)
    # Remove the trunk port from the vlan_lists
    trunk_port = cfg.get('driver simple_vlan', 'trunk_port')
    for vlan in returnee:
        if trunk_port in returnee[vlan]:
            returnee[vlan].remove(trunk_port)
    return returnee
