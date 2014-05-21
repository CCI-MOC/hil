"""A switch driver for the Dell Powerconnect

Currently the driver uses telnet to connect to the switch's console; in
the long term we want to be using SNMP.
"""

import os
import pexpect
import re

from haas.config import cfg

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
    #[.]* will handle end dots if any
    # this sequence terminates with #
    console.expect(r'[\r\n]+.+#')
    cmdPrompt = console.after
    cmdPrompt = cmdPrompt.strip(' \r\n\t')
    print('shellprompt ' + cmdPrompt)

    main_prompt = cmdPrompt
    #:-1 omits the last hash character
    config_prompt = re.escape(main_prompt[:-1] + '(config)#')
    if_prompt = re.escape(main_prompt[:-1] + '(config-if)#')
    main_prompt = re.escape(main_prompt)
    
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
    
