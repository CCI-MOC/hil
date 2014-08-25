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

"""A switch driver for the Dell Powerconnect

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

class Dell_Vlan(Model):
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


def apply_networking(net_map):
    for port_id in net_map:
        set_access_vlan(port_id, net_map[port_id])

def get_new_network_id(db):
    vlan = db.query(Dell_Vlan).filter_by(available = True).first()
    if not vlan:
        return None
    vlan.available = False
    returnee = str(vlan.vlan_no)
    return returnee

def free_network_id(db, net_id):
    vlan = db.query(Dell_Vlan).filter_by(vlan_no = net_id).first()
    if not vlan:
        pass
    vlan.available = True

def get_vlan_list():
    vlan_str = cfg.get('switch dell', 'vlans')
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
        db.add(Dell_Vlan(vlan))
    db.commit()

@no_dry_run
def set_access_vlan(port, vlan_id):
    # load the configuration:
    switch_ip = cfg.get('switch dell', 'ip')
    switch_user = cfg.get('switch dell', 'user')
    switch_pass = cfg.get('switch dell', 'pass')

    # connect to the switch, and log in:
    console = pexpect.spawn('telnet ' + switch_ip)
    console.expect('User Name:')
    console.sendline(switch_user)
    console.expect('Password:')
    console.sendline(switch_pass)

    #Regex to handle different prompt at switch 
    #[\r\n]+ will handle any newline
    #.+ will handle any character after newline 
    # this sequence terminates with #
    console.expect(r'[\r\n]+.+#')
    cmd_prompt = console.after
    cmd_prompt = cmd_prompt.strip(' \r\n\t')
    
    #:-1 omits the last hash character
    config_prompt = re.escape(cmd_prompt[:-1] + '(config)#')
    if_prompt = re.escape(cmd_prompt[:-1] + '(config-if)#')
    main_prompt = re.escape(cmd_prompt)
    
    # select the right interface:
    console.sendline('config')
    console.expect(config_prompt)
    console.sendline('int gi1/0/%s' % port)
    console.expect(if_prompt)

    if vlan_id is None:
        # turn the port off
        console.sendline('sw access vlan no')
    else:
        # set the vlan:
        console.sendline('sw access vlan %s' % vlan_id)
    console.expect(if_prompt)

    # set it to access mode:
    console.sendline('sw mode access')
    console.expect(if_prompt)

    # log out:
    console.sendline('exit')
    console.expect(config_prompt)
    console.sendline('exit')
    console.expect(main_prompt)
    console.sendline('exit')
    console.expect(pexpect.EOF)
    
