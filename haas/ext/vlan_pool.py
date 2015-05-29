"""VLAN based ``network_pool`` implementation."""

import logging

import haas.network_pool
from haas.network_pool import NetworkPool
from haas.model import Model
from sqlalchemy import Column, Integer, Boolean

class VlanPool(NetworkPool):
    """A pool of VLANs. The interface is as specified in ``NetworkPool``."""

    def get_new_network_id(self, db):
        vlan = db.query(Vlan).filter_by(available = True).first()
        if not vlan:
            return None
        vlan.available = False
        returnee = str(vlan.vlan_no)
        return returnee

    def free_network_id(self, db, net_id):
        vlan = db.query(Vlan).filter_by(vlan_no = net_id).first()
        if not vlan:
            logger = logging.getLogger(__name__)
            logger.error('vlan %s does not exist in database' % net_id)
            return
        vlan.available = True


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

haas.network_pool.network_pool = VlanPool()
