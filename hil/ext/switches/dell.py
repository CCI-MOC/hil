"""A switch driver for the Dell Powerconnect 5500 series.

Currently the driver uses telnet to connect to the switch's console; in
the long term we want to be using SNMP.
"""

import logging
from schema import Schema, Optional
import re

from hil.model import db, Switch
from hil.migrations import paths
from hil.ext.switches import _console
from hil.ext.switches._dell_base import _BaseSession
from os.path import dirname, join
from hil.errors import BadArgumentError
from hil.model import BigIntegerType
from hil.config import core_schema, string_is_bool

paths[__name__] = join(dirname(__file__), 'migrations', 'dell')
logger = logging.getLogger(__name__)

core_schema[__name__] = {
    Optional('save'): lambda s: string_is_bool(s)
}


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
        Schema({
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

    def get_capabilities(self):
        return ['nativeless-trunk-mode']


class _PowerConnect55xxSession(_BaseSession):
    """session object for the power connect 5500 series"""

    def __init__(self, config_prompt, if_prompt, main_prompt, switch, console):
        self.config_prompt = config_prompt
        self.if_prompt = if_prompt
        self.main_prompt = main_prompt
        self.switch = switch
        self.console = console

    @staticmethod
    def connect(switch):
        """connect to the switch, and log in."""

        console = _console.login(switch)

        # Send some string, so we expect the prompt again. Sending only new a
        # line doesn't work, it returns some unwanted ANSI sequences in
        # console.after
        # Eg; main_prompts looks like '\r\n\r\r\x1b[Kconsole#'
        # Here \x1b[K is unwanted and causes trouble parsing it.
        # Sending some other random string doesn't have this issue.
        console.sendline('some-unrecognized-command')
        prompts = _console.get_prompts(console)
        return _PowerConnect55xxSession(switch=switch,
                                        console=console,
                                        **prompts)

    def _set_terminal_lines(self, lines):
        if lines == 'unlimited':
            self._sendline('terminal datadump')
        elif lines == 'default':
            self._sendline('no terminal datadump')
