"""Super Class for Dell like drivers. """

import re
import logging
from hil.ext.switches.common import parse_vlans

from hil.ext.switches import _console

logger = logging.getLogger(__name__)


class _BaseSession(_console.Session):

    def enter_if_prompt(self, interface):
        self._sendline('config')
        self._sendline('int ' + interface)

    def exit_if_prompt(self):
        self._sendline('exit')
        self._sendline('exit')

    def enable_vlan(self, vlan_id):
        self._sendline('sw mode trunk')
        self._sendline('sw trunk allowed vlan add ' + vlan_id)

    def disable_vlan(self, vlan_id):
        self._sendline('sw trunk allowed vlan remove ' + vlan_id)

    def set_native(self, old, new):
        if old is not None:
            self.disable_vlan(old)
        self.enable_vlan(new)
        self._sendline('sw trunk native vlan ' + new)

    def disable_native(self, vlan_id):
        self.disable_vlan(vlan_id)
        self._sendline('sw trunk native vlan none')


    def get_port_networks(self, ports):
        port_configs = self._port_configs(ports)
        badchars = ' (Inactive)'
        network_list = []
        for k, v in port_configs.iteritems():
            non_natives = ''
            non_native_list = []
            # Get native vlan then remove junk if native not None
            native_vlan = v['Trunking Native Mode VLAN'].strip()
            if (native_vlan != 'none'):
                native_vlan = ''.join(c for c in native_vlan
                                      if c not in badchars)
            else:
                native_vlan = None
            # Get other vlans and parse out junk if not None
            trunk_vlans = v['Trunking VLANs Enabled'].strip()
            if (trunk_vlans != 'none'):
                non_natives = ''.join(c for c in trunk_vlans
                                      if c not in badchars)
                non_natives = non_natives.split('\r\n')
                non_natives = ','.join(non_natives)
                non_native_list = parse_vlans(non_natives)
            else:
                non_natives = None
            if native_vlan is not None:
                network_list.append(('vlan/native', native_vlan))
            for v in (non_native_list):
                if v != native_vlan:
                    network_list.append(('vlan/%s' % v, int(v)))
        return network_list

    def disable_port(self):
        self._sendline('sw trunk allowed vlan none')
        self._sendline('sw trunk native vlan none')

    def _port_configs(self, ports):
        result = {}
        for port in ports:
            result[port] = self._int_config(port.label)
        return result

    def _int_config(self, interface):
        """Collect information about the specified interface

        Returns a dictionary from the output of ``show int sw <interface>``.
        """

        alternatives = [
            r'More: .*',  # Prompt to press a key to continue
            r'Classification rules:\r\n',  # End
            r'[^ \t\r\n][^:]*:[^\n]*\n',   # Key:Value\r\n,
            r' [^\n]*\n',                  # continuation line (from k:v)
        ]
        self._sendline('show int sw %s' % interface)

        # Name is the first field:
        self.console.expect('Name: .*')
        k, v = self.console.after.split(':', 1)
        result = {k: v}
        while True:
            index = self.console.expect(alternatives)
            if index == 0:
                self.console.send(' ')
            elif index == 1:
                break
            elif index == 2:
                k, v = self.console.after.split(':', 1)
                result[k] = v
            elif index == 3:
                result[k] += self.console.after

        self.console.expect(self.main_prompt)
        return result

    def save_running_config(self):
        self._sendline('copy running-config startup-config')
        self.console.expect(['Overwrite file ', re.escape('(y/n) ')])
        self._sendline('y')
        self.console.expect(['Copy succeeded', 'Configuration Saved'])
        logger.debug('Copy succeeded')

    def get_config(self, config_type):
        self._set_terminal_lines('unlimited')
        self.console.expect(self.main_prompt)
        self._sendline('show ' + config_type + '-config')
        self.console.expect(self.main_prompt)
        config = self.console.before
        config = config.split("\n", 1)[1]
        self._set_terminal_lines('default')
        return config
