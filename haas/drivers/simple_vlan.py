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

This is for setups with a single switch.

This driver does not manage the trunked links between the switches.  Indeed,
it doesn't even know how they are set up.

The format of ports here is simply "[port_id]", where "port_id" is whatever
that switch's driver expects.  "switch_id" can be anything, and corresponds to
the description in the config file.

[general]
driver = simple_vlan

[driver simple_vlan]
switch = {switch: dell, ip: "192.168.0.2", user: "foo", pass: "bar"}

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
