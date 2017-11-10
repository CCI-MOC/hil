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
"""Super Class for Dell like drivers. """

import re
import logging

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
        num_re = re.compile(r'(\d+)')
        port_configs = self._port_configs(ports)
        result = {}
        for k, v in port_configs.iteritems():
            native = v['Trunking Native Mode VLAN'].strip()
            match = re.match(num_re, native)
            if match:
                # We need to call groups to get the part of the string that
                # actually matched, because it could include some junk on the
                # end, e.g. "100 (Inactive)".
                num_str = match.groups()[0]
                native = int(num_str)
            else:
                native = None
            networks = []
            range_str = v['Trunking VLANs Enabled']
            for range_str in v['Trunking VLANs Enabled'].split(','):
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
