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

"""A switch driver for VLAN-based setups using multiple non-stacked switches.

See the documentation for the haas.drivers package for a description of this
module's interface.

This is for setups where many switches are connected together with trunk
ports, and nodes are connected to various switches.  The switches can have
either the same model or different models---this driver can shell out to any
other appropriate driver.

This driver does not manage the trunked links between the switches.  Indeed,
it doesn't even know how they are set up.

The format of ports here is "[switch_name]::[port_id]".  "port_id" is whatever
that switch's driver expects.  "switch_name" can be anything, and corresponds
to the description in the config file.

haas.cfg should have, in the section "driver complex_vlan", the entry
'switches', with value a JSON-encoded list of dicts.  Each dict has fields
'switch' (the driver) and 'name' (the name used in port names), as well as any
others expected by the switch driver (e.g. Dell)

"""

import json
import importlib
from haas.config import cfg

# We are a VLAN-based driver with simple allocation
from haas.drivers.driver_tools.vlan import *

def apply_networking(net_map):
    switches = json.loads(cfg.get('driver complex_vlan', 'switch'))
    for switch in switches:
        submap = {}
        name = switch["name"]
        driver = importlib.import_module('haas.drivers.switches.' + switch["switch"])
        for net_entry in net_map:
            switch_id, port_id = net_entry.split("::")
            if switch_id == name:
                submap[port_id] = net_map[net_entry]
        driver.apply_networking(submap, switch)

def get_switch_vlans(vlan_list):
    switches = json.loads(cfg.get('driver complex_vlan', 'switch'))
    returnee = {}
    for vlan in vlan_list:
        returnee[vlan] = []
    for switch in switches:
        driver = importlib.import_module('haas.drivers.switches.' + switch['switch'])
        submap = driver.get_switch_vlans(switch, vlan_list)
        for vlan in submap:
            for port in submap[vlan]:
                returnee[vlan].append(switch['name'] + "::" + port)

    # Remove the trunk port from the vlan_lists
    trunk_ports = json.loads(cfg.get('driver complex_vlan', 'trunk_ports'))
    for vlan in returnee:
        for trunk_port in trunk_ports:
            if trunk_port in returnee[vlan]:
                returnee[vlan].remove(trunk_port)
    return returnee
