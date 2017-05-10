# Copyright 2013-2017 Massachusetts Open Cloud Contributors
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
"""A switch driver for the Dell Powerconnect 5500 series and N3000 series.

Currently the driver uses telnet to connect to the switch's console; in
the long term we want to be using SNMP.
"""

import pexpect
import re
import logging
import schema

from haas.model import db, Switch
from haas.migrations import paths
from haas.ext.switches import _console
from haas.ext.switches._dell_base import _base_session
from os.path import dirname, join

paths[__name__] = join(dirname(__file__), 'migrations', 'dell')
logger = logging.getLogger(__name__)


class PowerConnect55xx(Switch):
    api_name = 'http://schema.massopencloud.org/haas/v0/switches/' \
        'powerconnect55xx'

    __mapper_args__ = {
        'polymorphic_identity': api_name,
    }

    id = db.Column(db.Integer, db.ForeignKey('switch.id'), primary_key=True)
    hostname = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

    @staticmethod
    def validate(kwargs):
        schema.Schema({
            'username': basestring,
            'hostname': basestring,
            'password': basestring,
        }).validate(kwargs)

    def session(self):
        return _PowerConnect55xxSession.connect(self)


class DellN3000(Switch):
    api_name = 'http://schema.massopencloud.org/haas/v0/switches/' \
        'delln3000'

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
                                     lambda v: 0 <= v and v <= 4093,
                                     schema.Use(str)),
        }).validate(kwargs)

    def session(self):
        return _DellN3000Session.connect(self)


class _PowerConnect55xxSession(_base_session):
    """session object for the power connect 5500 series"""

    def __init__(self, config_prompt, if_prompt, main_prompt, switch, console):
        self.config_prompt = config_prompt
        self.if_prompt = if_prompt
        self.main_prompt = main_prompt
        self.switch = switch
        self.console = console

    def _sendline(self, line):
        logger.debug('Sending to switch %r: %r',
                     self.switch, line)
        self.console.sendline(line)

    @staticmethod
    def connect(switch):
        # connect to the switch, and log in:
        console = pexpect.spawn('telnet ' + switch.hostname)
        console.expect('User Name:')
        console.sendline(switch.username)
        console.expect('Password:')
        console.sendline(switch.password)

        logger.debug('Logged in to switch %r', switch)

        prompts = _console.get_prompts(console)
        return _PowerConnect55xxSession(switch=switch,
                                        console=console,
                                        **prompts)

    def _set_terminal_lines(self, lines):
        if lines == 'unlimited':
            self._sendline('terminal datadump')
        elif lines == 'default':
            self._sendline('no terminal datadump')


class _DellN3000Session(_base_session):
    """session object for the N300 series"""

    def __init__(self, config_prompt, if_prompt, main_prompt, switch, console,
                 dummy_vlan):
        self.config_prompt = config_prompt
        self.if_prompt = if_prompt
        self.main_prompt = main_prompt
        self.switch = switch
        self.console = console
        self.dummy_vlan = dummy_vlan

    def _sendline(self, line):
        logger.debug('Sending to switch` switch %r: %r',
                     self.switch, line)
        self.console.sendline(line)

    @staticmethod
    def connect(switch):
        # connect to the switch, and log in:
        console = pexpect.spawn('telnet ' + switch.hostname)
        console.expect('User:')
        console.sendline(switch.username)
        console.expect('Password:')
        console.sendline(switch.password)
        console.expect('>')
        console.sendline('en')

        logger.debug('Logged in to switch %r', switch)

        prompts = _console.get_prompts(console)
        # create the dummy vlan
        console.sendline('config')
        console.expect(prompts['config_prompt'])
        console.sendline('vlan ' + switch.dummy_vlan)
        console.sendline('exit')

        return _DellN3000Session(switch=switch,
                                 dummy_vlan=switch.dummy_vlan,
                                 console=console,
                                 **prompts)

    def disable_port(self):
        self._sendline('sw trunk allowed vlan add ' + self.dummy_vlan)
        self._sendline('sw trunk native vlan ' + self.dummy_vlan)
        self._sendline('sw trunk allowed vlan remove 1-4093')

    def disable_native(self, vlan_id):
        self.disable_vlan(vlan_id)
        # first set the dummy vlan as trunking vlan, then set that as it's
        # native, then remove that vlan from trunking vlans. otherwise the
        # switch won't let you set a native vlan that isn't added.
        self._sendline('sw trunk allowed vlan add ' + self.dummy_vlan)
        self._sendline('sw trunk native vlan ' + self.dummy_vlan)
        self._sendline('sw trunk allowed vlan remove ' + self.dummy_vlan)

    def _set_native(self, old_native, network_id, interface):
        # create the vlan that we need to set as native
        self._sendline('exit')
        self._sendline('vlan ' + network_id)
        self._sendline('exit')
        self._sendline('exit')
        self.enter_if_prompt(interface)
        # set the native vlan here
        self.set_native(old_native, network_id)

    def _int_config(self, interface):
        """Collect information about the specified interface

        Returns a dictionary from the output of ``show int sw <interfaces>``.
        """

        self._sendline('show int sw %s' % interface)
        self.console.expect('Port: .*')
        k, v = 'a', 'b'
        result = {k: v}
        key_lines = self.console.after.splitlines()
        del key_lines[-3:]
        for line in key_lines:
            k, v = line.split(':', 1)
            result[k] = v
        # FIXME: we shouldnt expect '', main_prompt should handle this
        self.console.expect([self.main_prompt, ''])
        return result

    def get_port_networks(self, ports):
        num_re = re.compile(r'(\d+)')
        port_configs = self._port_configs(ports)
        result = {}
        for k, v in port_configs.iteritems():
            native = v['Trunking Mode Native VLAN'].strip()
            match = re.match(num_re, native)
            if match:
                # We need to call groups to get the part of the string that
                # actually matched, because it could include some junk on the
                # end, e.g. "100 (Inactive)".
                num_str = match.groups()[0]
                native = int(num_str)
                if native == int(self.switch.dummy_vlan):
                    native = None
            else:
                native = None
            networks = []
            range_str = v['Trunking Mode VLANs Enabled']
            for range_str in v['Trunking Mode VLANs Enabled'].split(','):
                for num_str in range_str.split('-'):
                    num_str = num_str.strip()
                    match = re.match(num_re, num_str)
                    if match:
                        # There may be other tokens in the output, e.g.
                        # the string "(Inactive)" somteimtes appears.
                        # We should only use the value if it's an actual number
                        num_str = match.groups()[0]
                        networks.append(('vlan/%s' % num_str, int(num_str)))
            if native is not None:
                networks.append(('vlan/native', native))
            result[k] = networks
        return result
