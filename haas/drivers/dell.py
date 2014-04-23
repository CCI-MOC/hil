"""A switch driver for the Dell Powerconnect

Currently the driver uses telnet to connect to the switch's console; in
the long term we want to be using SNMP.
"""

import os
import pexpect
import re

from haas.config import get_value_from_config

def set_access_vlan(port, vlan_id):
    main_prompt = re.escape('console#')
    config_prompt = re.escape('console(config)#')
    if_prompt = re.escape('console(config-if)#')

    # load the configuration:
    switch_ip = get_value_from_config('switch dell', 'ip')
    switch_user = get_value_from_config('switch dell', 'user')
    switch_pass = get_value_from_config('switch dell', 'pass')

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
    
