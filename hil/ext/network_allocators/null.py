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
"""A null network allocator.

Network IDs are random and arbitrary. The only supported channel is "null".
"""

import uuid
from hil.network_allocator import NetworkAllocator, set_network_allocator


class NullNetworkAllocator(NetworkAllocator):
    """A Null network allocator.

    Conforms to the interface specified for its superclass, NetworkAllocator.
    """
    def get_new_network_id(self):
        return str(uuid.uuid1())

    def free_network_id(self, net_id):
        pass

    def populate(self):
        pass

    def legal_channels_for(self, net_id):
        return ["null"]

    def is_legal_channel_for(self, channel_id, net_id):
        return channel_id == "null"

    def get_default_channel(self):
        return "null"

    def validate_network_id(self, net_id):
        return True

    def claim_network_id(self, net_id):
        return

    def is_network_id_in_pool(self, net_id):
        return True


def setup(*args, **kwargs):
    """Register a NullNetworkAllocator as the network allocator."""
    set_network_allocator(NullNetworkAllocator())
