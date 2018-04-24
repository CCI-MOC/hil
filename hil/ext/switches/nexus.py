"""A switch driver for the Nexus 5500

Currently the driver uses telnet to connect to the switch's console; in the
long term we want to be using SNMP.
"""

import re
from schema import Schema, Optional, And, Use
import logging

from hil.model import db, Switch, Port
from hil.ext.switches import _console
from hil.errors import BadArgumentError
from os.path import join, dirname
from hil.migrations import paths
from hil.model import BigIntegerType
from hil.config import core_schema, string_is_bool
from hil.ext.switches.common import parse_vlans

logger = logging.getLogger(__name__)

paths[__name__] = join(dirname(__file__), 'migrations', 'nexus')

core_schema[__name__] = {
    Optional('save'): string_is_bool
}


class Nexus(Switch):
    """A Cisco Nexus switch."""

    api_name = 'http://schema.massopencloud.org/haas/v0/switches/nexus'

    __mapper_args__ = {
        'polymorphic_identity': api_name,
    }

    id = db.Column(BigIntegerType,
                   db.ForeignKey('switch.id'), primary_key=True)
    hostname = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    dummy_vlan = db.Column(db.String, nullable=False)

    @staticmethod
    def validate(kwargs):
        Schema({
            'username': basestring,
            'hostname': basestring,
            'password': basestring,
            'dummy_vlan': And(Use(int),
                              lambda v: 0 < v and v <= 4096,
                              Use(str)),
        }).validate(kwargs)

    def session(self):
        return _Session.connect(self)

    @staticmethod
    def validate_port_name(port):
        """
        Valid port names for this switch are of the form: Ethernet1/12,
        ethernet1/12, Ethernet1/0/10, or ethernet1/0/10
        """

        val = re.compile(r'^(E|e)thernet\d+/\d+(/\d+)?$')
        if not val.match(port):
            raise BadArgumentError("Invalid port name. Valid port names for "
                                   "this switch are of the form: Ethernet1/12"
                                   " ethernet1/12, Ethernet1/0/10, or"
                                   " ethernet1/0/10")
        return

    def get_capabilities(self):
        return ['nativeless-trunk-mode']


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
        self._sendline('config terminal')
        self._sendline('int %s' % interface)

    def exit_if_prompt(self):
        self._sendline('exit')
        self._sendline('exit')

    def enable_vlan(self, vlan_id):
        self._sendline('sw')
        self._sendline('sw mode trunk')
        self._sendline('sw trunk allowed vlan add %s' % vlan_id)

    def disable_vlan(self, vlan_id):
        self._sendline('sw trunk allowed vlan remove %s' % vlan_id)

    def set_native(self, old, new):
        if old is not None:
            self.disable_vlan(old)
        self._sendline('sw trunk native vlan %s' % new)
        self.enable_vlan(new)

    def disable_native(self, vlan_id):
        self.disable_vlan(vlan_id)
        self._sendline('sw trunk native vlan ' + self.dummy_vlan)

    @staticmethod
    def connect(switch):
        """Connect to the switch."""

        console = _console.login(switch)

        # send a new line so that we can "expect" a prompt again if we already
        # matched when logged in using pubkey
        console.sendline('')
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
        self._sendline('show int sw')

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
            # sometimes switch has custom interface names, so we skip those
            if match is None:
                continue
            # TODO: We should verify there is in fact a match (there always
            # should be, but let's be paranoid).
            switch, port = match.groups()
            names_result['Ethernet%s/%s' % (switch, port)] = v

        result = {}
        for port in ports:
            result[port] = names_result[port.label]

        return result


    def get_port_networks(self, ports):
          port_configs = self._port_configs(ports)
          network_list = []
          for k, v in port_configs.iteritems():
              non_natives = ''
              non_native_list = []
              # Get native vlan then remove junk if native not None
              native_vlan = v['Trunking Native Mode VLAN'].strip()
              if native_vlan == int(self.switch.dummy_vlan):
                  native_vlan = None
              elif native_vlan != 'none':
                  temp = ''
                  for c in native_vlan:
                      if c == ' ':
                          break
                      temp += c
                  native_vlan = temp
              else:
                  native_vlan = None
              # Get other vlans
              trunk_vlans = v['Trunking VLANs Allowed'].strip()
              if trunk_vlans != 'none':
                  non_native_list = parse_vlans(trunk_vlans)
              else:
                  non_natives = None
              if native_vlan is not None:
                  network_list.append(('vlan/native', native_vlan))
              for v in (non_native_list):
                  if v != native_vlan:
                      network_list.append(('vlan/%s' % v, int(v)))
          return network_list

    def save_running_config(self):
        self._sendline('copy running-config startup-config')
        self.console.expect('Copy complete')
        logger.debug('Copy succeeded')

    def get_config(self, config_type):
        self._set_terminal_lines('unlimited')
        self.console.expect(r'[\r\n]+.+# ')
        self._sendline('show ' + config_type + '-config')
        self.console.expect(r'[\r\n]+.+# ')
        config = self.console.after

        # The config files always have some lines in the beginning that we
        # need to remove otherwise the comparison would fail. Here's a sample:
        # !Command: show running-config
        # !Time: Tue Apr 25 16:36:40 2017
        # version 6.0(2)A1(1a)
        # hostname the-switch
        # feature telnet
        # username admin password 5 XXXXXXXX  role network-admin
        # ssh key rsa 2048
        lines_to_remove = 0
        for line in config.splitlines():
            if 'username' in line:
                break
            lines_to_remove += 1

        config = config.split("\n", lines_to_remove)[lines_to_remove]
        self._set_terminal_lines('default')
        return config

    def disable_port(self):
        self._sendline('sw trunk allowed vlan none')
        self._sendline('sw trunk native vlan ' + self.dummy_vlan)
