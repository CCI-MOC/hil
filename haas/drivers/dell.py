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

@no_dry_run
def set_access_vlan(port, vlan_id):
    main_prompt = re.escape('console#')
    config_prompt = re.escape('console(config)#')
    if_prompt = re.escape('console(config-if)#')

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
    console.expect(main_prompt)

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
    
