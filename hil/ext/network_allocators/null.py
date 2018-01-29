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
