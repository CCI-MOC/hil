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

"""A VLAN-based null switch driver.  Network IDs are allocated from a VLAN
pool.  Applying the network state does nothing.

For unit testing purposes.
"""

# We are a VLAN-based driver with simple allocation
from haas.drivers.driver_tools.vlan import *

def apply_networking(net_map):
    # The following code does nothing, except for check that the net_map is in
    # fact a map that can be iterated over.  This is how it's used in the
    # 'dell' plugin, and likely in most VLAN-based plugins.  This can help
    # check for bugs in haas/api.py
    for port in net_map:
        net = net_map[port]
