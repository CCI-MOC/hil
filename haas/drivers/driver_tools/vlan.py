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

"""This module contains a set of tools that are used by specific switch
drivers.  Functions contained within this module are generic, and are
not specific to any one switch."""

import logging
from sqlalchemy import *
from haas.model import *
from haas import network_pool



def get_new_network_id(db):
    return network_pool.network_pool.get_new_network_id(db)


def free_network_id(db, net_id):
    return network_pool.network_pool.free_network_id(db, net_id)


def get_vlan_list():
    vlan_str = cfg.get('vlan', 'vlans')
    returnee = []
    for r in vlan_str.split(","):
        r = r.strip().split("-")
        if len(r) == 1:
            returnee.append(int(r[0]))
        else:
            returnee += range(int(r[0]), int(r[1])+1)
    return returnee


def init_db(create=False):
    # I'm importing this here so we don't unduly invalidate testing of the
    # extension mechansim. This is a temporary hack, soon the rest of this
    # module will be moved to the network pool extension we're importing.
    # XXX
    from haas.ext import vlan_pool
    if not create:
        return
    vlan_list = get_vlan_list()
    db = Session()
    for vlan in vlan_list:
        db.add(vlan_pool.Vlan(vlan))
    db.commit()
