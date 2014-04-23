"""A switch driver for the Dell Powerconnect

Currently the driver uses telnet to connect to the switch's console; in
the long term we want to be using SNMP.
"""

import os
import pexpect
import re

from haas.config import get_value_from_config, register_callback

@register_callback
def validate_config():
    """ Returns True if the config file has valid data, False (w/ the error
        string) otherwise.

        This is a sample implementation; it just checks if the ip address
        is present and is in the correct format.
        TODO: Add similar checks for other options for the Dell driver.
    """
    ip = get_value_from_config('switch dell', 'ip')
    if not(ip):
        return (False, "[Dell Driver]: Missing IP address in the config file")
    ip_regex = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    if re.match(ip_regex, ip):
        return (True, None)
    else:
        return (False, "[Dell Driver]: Invalid IP address: " + ip + " in the config file")

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
    
