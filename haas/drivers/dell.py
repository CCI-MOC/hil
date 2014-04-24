"""A switch driver for the Dell Powerconnect

Currently the driver uses telnet to connect to the switch's console; in
the long term we want to be using SNMP.
"""

import os
import pexpect
import re
import socket

from haas.config import cfg, register_callback, BadConfigError
from haas.utils import is_valid_ip

@register_callback
def validate_config():
    """ Returns True if the config file has valid data, False (w/ the error
        string) otherwise.

        This  implementation checks for a valid ip address in a "switch dell"
        section in the config.
        TODO: Add similar checks for other options for the Dell driver.
    """
    if not(cfg.has_section('switch dell')):
        return (True, None)
    if not(cfg.has_option('switch dell', 'ip')):
        return (False, "[Dell Driver]: Missing IP address in the config file")
    ip = cfg.get('switch dell', 'ip')
    if is_valid_ip(ip):
        return (True, None)
    else:
        return (False, "[Dell Driver]: Invalid IP address: " + ip + " in the config file")

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
    
