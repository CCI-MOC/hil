# Copyright 2013-2014 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language
# governing permissions and limitations under the License.

"""A switch driver for the Nexus 5500

Currently the driver uses telnet to connect to the switch's console; in the
long term we want to be using SNMP.
"""

import pexpect
import re
import schema
import logging

from haas.model import db, Switch
from haas.ext.switches import _console

logger = logging.getLogger(__name__)


class Nexus(Switch):
    api_name = 'http://schema.massopencloud.org/haas/v0/switches/nexus'

    __mapper_args__ = {
        'polymorphic_identity': api_name,
    }

    id = db.Column(db.Integer, db.ForeignKey('switch.id'), primary_key=True)
    hostname = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    dummy_vlan = db.Column(db.String, nullable=False)

    @staticmethod
    def validate(kwargs):
        schema.Schema({
            'username': basestring,
            'hostname': basestring,
            'password': basestring,
            'dummy_vlan': schema.And(schema.Use(int),
                                     lambda v: 0 <= v and v <= 4096,
                                     schema.Use(str)),
        }).validate(kwargs)

    def session(self):
        return _Session.connect(self)


class _Session(_console.Session):

    def __init__(self, config_prompt, if_prompt, main_prompt, switch, console,
                 dummy_vlan):
        self.config_prompt = config_prompt
        self.if_prompt = if_prompt
        self.main_prompt = main_prompt
        self.switch = switch
        self.console = console
        self.dummy_vlan = dummy_vlan

    def enter_if_prompt(self, interface):
        self.console.sendline('config terminal')
        self.console.sendline('int %s' % interface)

    def exit_if_prompt(self):
        self.console.sendline('exit')
        self.console.sendline('exit')

    def enable_vlan(self, vlan_id):
        self.console.sendline('sw')
        self.console.sendline('sw mode trunk')
        self.console.sendline('sw trunk allowed vlan add %s' % vlan_id)

    def disable_vlan(self, vlan_id):
        self.console.sendline('sw trunk allowed vlan remove %s' % vlan_id)

    def set_native(self, old, new):
        if old is not None:
            self.disable_vlan(old)
        self.console.sendline('sw trunk native vlan %s' % new)
        self.enable_vlan(new)

    def disable_native(self, vlan_id):
        self.disable_vlan(vlan_id)
        self.console.sendline('sw trunk native vlan ' + self.dummy_vlan)

    def disconnect(self):
        self.console.sendline('exit')

    @staticmethod
    def connect(switch):
        console = pexpect.spawn('telnet ' + switch.hostname)
        console.expect('login: ')
        console.sendline(switch.username)
        console.expect('Password: ')
        console.sendline(switch.password)

        prompts = _console.get_prompts(console)

        return _Session(console=console,
                        dummy_vlan=switch.dummy_vlan,
                        switch=switch,
                        **prompts)

    def _port_configs(self, ports):
        alternatives = [
            re.escape(r'--More--'),
            r'Name:[^\n]*\n',
            r'  [A-Z][^:]*:[^\n]*\n',
            r'[\r\n]+.+# ',
        ]
        self.console.sendline('show int sw')

        # Find the first interface name
        self.console.expect(alternatives[1])

        _, interface = self.console.after.split(':', 1)
        interface = interface.strip()
        info = {interface: {}}

        while True:
            index = self.console.expect(alternatives)
            if index == 0:
                self.console.send(' ')
            elif index == 1:
                _, interface = self.console.after.split(':', 1)
                interface = interface.strip()
                info[interface] = {}
            elif index == 2:
                k, v = self.console.after.split(':', 1)
                info[interface][k.strip()] = v.strip()
            elif index == 3:
                break

        # The output of show int sw calls things "EthernetX/YY", but
        # everything else calls things "ethernet X/YY". Let's do the conversion
        # here.
        names_result = {}
        pattern = re.compile(r'Ethernet(\d+)/(\d+)')
        for k, v in info.iteritems():
            match = re.match(pattern, k)
            # TODO: We should verify there is in fact a match (there always
            # should be, but let's be paranoid).
            switch, port = match.groups()
            names_result['ethernet %s/%s' % (switch, port)] = v

        result = {}
        for port in ports:
            result[port] = names_result[port.label]

        return result

    def get_port_networks(self, ports):
        num_re = re.compile(r'(\d+)')
        port_configs = self._port_configs(ports)
        result = {}

        for k, v in port_configs.iteritems():
            networks = []
            if 'Trunking Native Mode VLAN' not in v:
                # XXX (probable BUG): For some reason the last port on the
                # switch sometimes isn't read correctly. For now just don't use
                # that port for the test suite, and will skip it if this
                # happens.
                continue
            native = v['Trunking Native Mode VLAN'].strip()
            match = re.match(num_re, native)
            if match:
                num_str = match.groups()[0]
                native = int(num_str)
                if native == int(self.switch.dummy_vlan):
                    native = None
            else:
                native = None
            for range_str in v['Trunking VLANs Allowed'].split(','):
                # XXX TODO make this actualy interpret e.g. 2-7 as a *range*
                for num_str in range_str.split('-'):
                    num_str = num_str.strip()
                    match = re.match(num_re, num_str)
                    if match:
                        # There may be other tokens in the output, e.g.
                        # the string "(Inactive)" somteimtes appears.
                        # We should only use the value if it's an actual
                        # number.
                        num_str = match.groups()[0]
                        networks.append(('vlan/%s' % num_str, int(num_str)))

            if native is not None:
                networks.append(('vlan/native', native))
            result[k] = networks
        return result
