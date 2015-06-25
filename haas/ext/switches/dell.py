# Copyright 2013-2015 Massachusetts Open Cloud Contributors
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
"""A switch driver for the Dell Powerconnect 5500 series.

Currently the driver uses telnet to connect to the switch's console; in
the long term we want to be using SNMP.
"""

import pexpect
import re
import schema
from sqlalchemy import Column, ForeignKey, Integer, String

from haas.model import Switch, NetworkAttachment

_CHANNEL_RE = re.compile(r'vlan/(\d+)')


class PowerConnect55xx(Switch):
    api_name = 'http://schema.massopencloud.org/haas/switches/powerconnect55xx'

    id = Column(Integer, ForeignKey('switch.id'), primary_key=True)
    hostname = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)

    def validate(self, kwargs):
        schema.Schema({
            'username': basestring,
            'hostname': basestring,
            'password': basestring,
        }).validate(kwargs)

    def session(self):
        return _Session.connect(self)


class _Session(object):

    def __init__(self, config_prompt, if_prompt, main_prompt):
        self.config_prompt = config_prompt
        self.if_prompt     = if_prompt
        self.main_prompt   = main_prompt
        self.switch        = switch

    @staticmethod
    def connect(switch):
        # connect to the switch, and log in:
        console = pexpect.spawn('telnet ' + switch.hostname)
        console.expect('User Name:')
        console.sendline(switch.username)
        console.expect('Password:')
        console.sendline(switch.password)

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

        return _Session(config_prompt=config_prompt,
                        if_prompt=if_prompt,
                        main_prompt=main_prompt,
                        switch=switch)

    def apply_networking(self, action):
        interface = action.nic.port.label
        channel   = action.channel

        self.console.sendline('int ' + interface)
        self.console.expect(self.if_prompt)

        if channel == 'vlan/native':
            if new_network is None:
                old_attachment = NetworkAttachment.query\
                    .filter_by(channel='vlan/native', nic=action.nic).first()
                if old_attachment is not None:
                    self.console.sendline('sw trunk vlan allowed remove ' +
                                          old_attachment.network.network_id)
                self.console.sendline('sw trunk vlan native none')
            else:
                self.console.sendline('sw trunk vlan allowed add ' + new_network.network_id)
                self.console.sendline('sw trunk vlan native ' + new_network.network_id)
        else:
            match = re.match(_CHANNEL_RE, channel)
            # TODO: I'd be more okay with this assertion if it weren't possible
            # to mis-configure HaaS in a way that triggers this; currently the
            # administrator needs to line up the network allocator with the
            # switches; this is unsatisfactory. --isd
            assert match is not None, "HaaS passed an invalid channel to the switch!"
            vlan_id = match.groups()[0]
            if network is None:
                self.console.sendline('sw trunk vlan allowed remove ' + vlan_id)
            else:
                assert network == vlan_id
                self.console.sendline('sw trunk vlan allowed add ' + vlan_id)

        self.console.expect(self.if_prompt)
        # for good measure:
        self.console.sendline('sw mode trunk')

        self.console.expect(self.if_prompt)
        self.console.sendline('exit')
        self.console.expect(self.config_prompt)

    def disconnect(self):
        self.console.sendline('exit')
        self.console.expect(self.main_prompt)
        self.console.sendline('exit')
        self.console.expect(pexpect.EOF)


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
    vlan_cfgs = {}
    # This regex matches the notation for ports on the Dell switch.  For
    # example, 'gi1/0/24'
    regex = re.compile(r'gi\d+\/\d+\/\d+-?\d?\d?')
    for vlan in vlan_list:
        console.sendline('show vlan tag %d' % vlan)
        console.expect(cmd_prompt)
        vlan_cfgs[vlan] = regex.findall(console.before)

    # close session
    console.sendline('exit')
    console.expect(pexpect.EOF)

    return vlan_cfgs
