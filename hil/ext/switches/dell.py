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
"""A switch driver for the Dell Powerconnect 5500 series.

Currently the driver uses telnet to connect to the switch's console; in
the long term we want to be using SNMP.
"""

import pexpect
import logging
import schema
import re

from hil.model import db, Switch
from hil.migrations import paths
from hil.ext.switches import _console
from hil.ext.switches._dell_base import _BaseSession
from os.path import dirname, join
from hil.errors import BadArgumentError
from hil.model import BigIntegerType

paths[__name__] = join(dirname(__file__), 'migrations', 'dell')
logger = logging.getLogger(__name__)


class PowerConnect55xx(Switch):
    """Dell powerconnect 5500 series switch."""

    api_name = 'http://schema.massopencloud.org/haas/v0/switches/' \
        'powerconnect55xx'

    __mapper_args__ = {
        'polymorphic_identity': api_name,
    }

    id = db.Column(BigIntegerType,
                   db.ForeignKey('switch.id'), primary_key=True)
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

    @staticmethod
    def validate_port_name(port):
        """
        Valid port names for this switch are of the form gi1/0/11,
        te1/0/12, gi1/12, or te1/3
        """

        val = re.compile(r'^(gi|te)\d+/\d+(/\d+)?$')
        if not val.match(port):
            raise BadArgumentError("Invalid port name. Valid port names for "
                                   "this switch are of the form gi1/0/11, "
                                   "te1/0/12, gi1/12, or te1/3")
        return


class _PowerConnect55xxSession(_BaseSession):
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
        """connect to the switch, and log in."""
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
