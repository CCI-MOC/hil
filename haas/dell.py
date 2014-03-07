#! /usr/bin/python
import os
import pexpect
import re

from haas.config import cfg

#def set_access_vlan(port, vlan_id):
#    """sets the given port number to access mode, with the given vlan_id."""
#    # TODO: we aren't really doing much in the way of error checking here.
#    def _backout(f):
#        """Back out to the top level prompt."""
#        for _ in range(3):
#            # On the dell, extra exit commands are ignored. we never delve more
#            # than three prompts in, so this should be enough.
#            f.write("exit\n")
#
#    with open('/dev/ttyS0', 'w') as f:
#        _backout(f)
#
#        # find our way to the prompt for this port:
#        f.write("enable\n")
#        f.write("config\n")
#        f.write("int gi1/0/%d\n" % port)
#
#        # set the vlan
#        f.write("sw access vlan %d\n" % vlan_id)
#
#        # set the port to access mode
#        f.write("sw mode access\n")
# 
#        # Just for good measure:
#        _backout(f)

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
    
