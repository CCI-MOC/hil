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


from haas.dev_support import no_dry_run

from haas.drivers.driver_tools.vlan import *

@no_dry_run
def apply_networking(net_map, config):
    def set_access_vlan(port, vlan_id):
        """Set a port to access a given vlan.

        This function expects to be called while in the config prompt, and
        leaves you there when done.
        """
        console.sendline('int %s' % port)
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

        # back out to config_prompt
        console.sendline('exit')
        console.expect(config_prompt)

    # load the configuration:
    switch_ip = config["ip"]
    switch_user = config["user"]
    switch_pass = config["pass"]

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

    # For each port, set it
    for port_id in net_map:
        set_access_vlan(port_id, net_map[port_id])

    # log out
    console.sendline('exit')
    console.expect(main_prompt)
    console.sendline('exit')
    console.expect(pexpect.EOF)


# This doesn't get @no_dry_run, because returning None here is a bad idea
def get_switch_vlans(config, vlan_list):
    # load the configuration:
    switch_ip = config['ip']
    switch_user = config['user']
    switch_pass = config['pass']

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

    # get possible vlans from config
    vlan_cfgs = []
    for vlan in get_vlan_list():
        console.sendline('show vlan tag %d' % vlan)
        console.expect(cmd_prompt)
        vlan_cfgs.append(console.before)

    # close session
    console.sendline('exit')
    console.expect(pexpect.EOF)

    return vlan_cfgs
