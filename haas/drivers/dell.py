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
    vlan_no = Column(Integer, nullable=False)
    available = Column(Boolean, nullable=False)

    def __init__(self, vlan_no):
        self.vlan_no = vlan_no
        self.available = True
        # XXX: This is pretty gross; it arguably doesn't even make sense for
        # Vlan to have a label, but we need to do some refactoring for that.
        self.label = str(vlan_no)


def apply_network(net_map):
    for port_id, vlan_id in net_map:
        set_access_vlan(port_id, vlan_id)

def get_new_network_id():
    db = Session()
    vlan = db.query(Dell_Vlan).filter_by(available = True).first()
    if not vlan:
        return None
    vlan.avilable = False
    returnee = vlan.vlan_no
    db.commit()
    return returnee

def free_network_id(net_id):
    db = Session()
    vlan = db.query(Dell_Vlan).filter_by(vlan_no = net_id).first()
    if not vlan:
        pass
    vlan.available = True
    db.commit()

def init_db():
    db = Session()
    for i in range(100, 110):
        db.add(Dell_Vlan(i))
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
    console.sendline('int gi1/0/%d' % port)
    console.expect(if_prompt)

    # set the vlan:
    console.sendline('sw access vlan %d' % vlan_id)
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
    
