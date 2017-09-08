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
"""Common functionality for switches with a cisco-like console."""

from abc import ABCMeta, abstractmethod
from hil.model import Port, NetworkAttachment, SwitchSession
import re
from hil.config import cfg

_CHANNEL_RE = re.compile(r'vlan/(\d+)')


class Session(SwitchSession):
    """Common base class for sessions in console-based drivers."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def enter_if_prompt(self, interface):
        """Navigate from the main prompt to the prompt for configuring
        ``interface``.
        """

    @abstractmethod
    def exit_if_prompt(self):
        """Navigate back to the main prompt from an interface prompt."""

    @abstractmethod
    def enable_vlan(self, vlan_id):
        """Enable ``vlan_id`` for the current interface.

        For this to work, the session must be at an interface prompt (which is
        the "current interface"). See ``enter_if_prompt`` and
        ``exit_if_prompt``.
        """

    @abstractmethod
    def disable_vlan(self, vlan_id):
        """Like ``enable_vlan``, but disables the vlan, rather than enabling
        it.
        """

    @abstractmethod
    def set_native(self, old, new):
        """Set the native vlan for the current interface to ``new``.

        ``old`` must be the previous native vlan, or None if there was no
        previous native.
        """

    @abstractmethod
    def disable_native(self, vlan_id):
        """Disable the native vlan.

        ``vlan_id`` is the vlan id of the current native vlan.
        """

    @abstractmethod
    def disable_port(self):
        """Disable all vlans on the current port."""

    @abstractmethod
    def disconnect(self):
        """End the session. Must be at the main prompt."""

    def modify_port(self, port, channel, new_network):
        interface = port
        port = Port.query.filter_by(label=port,
                                    owner_id=self.switch.id).one()

        self.enter_if_prompt(interface)
        self.console.expect(self.if_prompt)

        if channel == 'vlan/native':
            old_native = NetworkAttachment.query.filter_by(
                channel='vlan/native',
                nic_id=port.nic.id).one_or_none()
            if old_native is not None:
                old_native = old_native.network.network_id

            if new_network is not None:
                self.set_native(old_native, new_network)
            elif old_native is not None:
                self.disable_native(old_native)
        else:
            match = re.match(_CHANNEL_RE, channel)
            # TODO: I'd be more okay with this assertion if it weren't possible
            # to mis-configure HIL in a way that triggers this; currently the
            # administrator needs to line up the network allocator with the
            # switches; this is unsatisfactory. --isd
            assert match is not None, "HIL passed an invalid channel to the" \
                "switch!"
            vlan_id = match.groups()[0]
            if new_network is None:
                self.disable_vlan(vlan_id)
            else:
                assert new_network == vlan_id
                self.enable_vlan(vlan_id)

        self.exit_if_prompt()
        self.console.expect(self.config_prompt)

    def revert_port(self, port):
        self.enter_if_prompt(port)
        self.console.expect(self.if_prompt)

        self.disable_port()

        self.exit_if_prompt()
        self.console.expect(self.config_prompt)

    def _should_save(self, switch_type):
        """checks the config file to see if switch should save or not"""

        switch_ext = 'hil.ext.switches.' + switch_type
        if cfg.has_option(switch_ext, 'save'):
            if not cfg.getboolean(switch_ext, 'save'):
                return False
        return True

    def _set_terminal_lines(self, lines):
        """set the terminal lines to unlimited or default"""

        if lines == 'unlimited':
            self.console.sendline('terminal length 0')
        elif lines == 'default':
            self.console.sendline('terminal length 40')


def get_prompts(console):
        """Determine the prompts used by the console.

        console should be a pexpect connection.

        The return value is a dictionary mapping prompt names to regexes
        matching them. The keys are:

            * config_prompt
            * if_prompt
            * main_prompt
        """
        # Regex to handle different prompt at switch
        # [\r\n]+ will handle any newline
        # .+ will handle any character after newline
        # this sequence terminates with #
        console.expect(r'[\r\n]+.+#')
        cmd_prompt = console.after.split('\n')[-1]
        cmd_prompt = cmd_prompt.strip(' \r\n\t')

        # :-1 omits the last hash character
        return {
            'config_prompt': re.escape(cmd_prompt[:-1] + '(config)#'),
            'if_prompt': re.escape(cmd_prompt[:-1]) + '\(config\\-if[^)]*\)#',
            'main_prompt': re.escape(cmd_prompt),
        }
