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


class Vlan(Model):
    """A VLAN for the Dell switch

    This is used to track which vlan numbers are available; when a Network is
    created, it must allocate a Vlan, to ensure that:

    1. The VLAN number it is using is unique, and
    2. The VLAN number is actually allocated to the HaaS; on some deployments we
       may have specific vlan numbers that we are allowed to use.
    """
    vlan_no = Column(Integer, nullable=False, unique=True)
    available = Column(Boolean, nullable=False)

    def __init__(self, vlan_no):
        self.vlan_no = vlan_no
        self.available = True
        # XXX: This is pretty gross; it arguably doesn't even make sense for
        # Vlan to have a label, but we need to do some refactoring for that.
        self.label = str(vlan_no)


def get_new_network_id(db):
    vlan = db.query(Vlan).filter_by(available = True).first()
    if not vlan:
        return None
    vlan.available = False
    returnee = str(vlan.vlan_no)
    return returnee


def free_network_id(db, net_id):
    vlan = db.query(Vlan).filter_by(vlan_no = net_id).first()
    if not vlan:
        logger = logging.getLogger(__name__)
        logger.error('vlan %s does not exist in database' % net_id)
        return
    vlan.available = True


def get_network_channels(db, net_id):
    vlan_num = int(net_id)
    return ['native', vlan_num]


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
    if not create:
        return
    vlan_list = get_vlan_list()
    db = Session()
    for vlan in vlan_list:
        db.add(Vlan(vlan))
    db.commit()
