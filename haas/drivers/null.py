"""A null switch driver.  Network IDs are random and arbitrary.  Applying the
network state does nothing.

For unit testing purposes.
"""

import uuid

def apply_networking(net_map):
    for port in net_map:
        net = net_map[port]

def get_new_network_id(db):
    return str(uuid.uuid1())

def free_network_id(db, net_id):
    pass

def init_db():
    pass
