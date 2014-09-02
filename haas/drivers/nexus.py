# Copyright 2013-2014 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language
# governing permissions and limitations under the License.
"""A switch driver for the Nexus 5500
See the documentation for the haas.drivers package for a description of this
module's interface.
Currently the driver uses telnet to connect to the switch's console; in
the long term we want to be using SNMP.
"""
import os
import pexpect
import re
from haas.config import cfg
from haas.dev_support import no_dry_run
from haas.model import Model, Session
from sqlalchemy import *
class Nexus_Vlan(Model):
    """A VLAN for the Cisco Nexus switch
       This is used to track which vlan numbers are available; when a Network is
       created, it must allocate a Vlan, to ensure that:
       1. The VLAN number it is using is unique, and
       2. The VLAN number is actually allocated to the HaaS; on some deployments we
       may have specific vlan numbers that we are allowed to use.
       This code currently only works if there is only one Nexus switch. 
       This is because the Nexus switch does not support switch stacking. 
    """
    vlan_no = Column(Integer, nullable=False, unique=True)
    available = Column(Boolean, nullable=False)
    def __init__(self, vlan_no):
        self.vlan_no = vlan_no
        self.available = True
        # XXX: This is pretty gross; it arguably doesn't even make sense for
        # Vlan to have a label, but we need to do some refactoring for that.
        self.label = str(vlan_no)
@no_dry_run
def apply_networking(net_map):
    def set_access_vlan(port, vlan_id):
        """Set a port to access a given vlan.

        This function expects to be called while in the config prompt, and
        leaves you there when done.
        """
        console.sendline('int ethernet 1/%s' % port)
        # set it first to switch mode then to access mode:
        console.expect(r'[\r\n]+.+# ')
        console.sendline('sw')
        console.expect(r'[\r\n]+.+# ')
        console.sendline('sw mode access')
        console.expect(r'[\r\n]+.+# ')

        if vlan_id is None:
            # turn the port off
            console.sendline('no sw')
        else:
            # set the vlan:
            console.sendline('sw access vlan %s' % vlan_id)
        console.expect(r'[\r\n]+.+# ')
        # back out to config_prompt
        console.sendline('exit')
        console.expect(r'[\r\n]+.+# ')

    nexus_ip = cfg.get('switch nexus', 'ip')
    nexus_user = cfg.get('switch nexus', 'user')
    nexus_pass = cfg.get('switch nexus', 'pass')
    try:
       console = pexpect.spawn('telnet ' + nexus_ip)
       console.expect('login: ')
       console.sendline(nexus_user)
       console.expect('password: ')
       console.sendline(nexus_pass)
       console.expect(r'[\r\n]+.+# ')
       console.sendline('config terminal')
       console.expect(r'[\r\n]+.+# ')

       for port_id in net_map:
            set_access_vlan(port_id, net_map[port_id])

    except IOError as e:
        print "Connection error while connecting to the Nexus switch({0}): {1}".format(e.errno, e.strerror)
    except:
        print "Unexpected error while connecting to the Nexus switch:", sys.exc_info()[0]
        raise
        sys.Exit(1)



def get_new_network_id(db):
    vlan = db.query(Nexus_Vlan).filter_by(available = True).first()
    if not vlan:
        return None
    vlan.available = False
    returnee = str(vlan.vlan_no)
    return returnee

def free_network_id(db, net_id):
    vlan = db.query(Nexus_Vlan).filter_by(vlan_no = net_id).first()
    if not vlan:
        pass
    vlan.available = True

def get_vlan_list():
    vlan_str = cfg.get('switch nexus', 'vlans')
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
        db.add(Nexus_Vlan(vlan))
    db.commit()

