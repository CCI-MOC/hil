"""VLAN based ``network_allocator`` implementation."""

import logging

from haas.network_allocator import NetworkAllocator, set_network_allocator
from haas.model import AnonModel, Session
from haas.config import cfg
from sqlalchemy import Column, Integer, Boolean


def _get_vlan_list():
    vlan_str = cfg.get('vlan', 'vlans')
    returnee = []
    for r in vlan_str.split(","):
        r = r.strip().split("-")
        if len(r) == 1:
            returnee.append(int(r[0]))
        else:
            returnee += range(int(r[0]), int(r[1])+1)
    return returnee


class VlanAllocator(NetworkAllocator):
    """A allocator of VLANs. The interface is as specified in ``NetworkAllocator``."""

    def get_new_network_id(self, db):
        vlan = db.query(Vlan).filter_by(available=True).first()
        if not vlan:
            return None
        vlan.available = False
        returnee = str(vlan.vlan_no)
        return returnee

    def free_network_id(self, db, net_id):
        vlan = db.query(Vlan).filter_by(vlan_no=net_id).first()
        if not vlan:
            logger = logging.getLogger(__name__)
            logger.error('vlan %s does not exist in database' % net_id)
            return
        vlan.available = True

    def populate(self, db):
        vlan_list = _get_vlan_list()
        for vlan in vlan_list:
            db.add(Vlan(vlan))
        db.commit()


class Vlan(AnonModel):
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


def setup(*args, **kwargs):
    set_network_allocator(VlanAllocator())
