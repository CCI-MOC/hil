# Copyright 2016 Massachusetts Open Cloud Contributors
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

"""A switch driver for Brocade NOS.

Uses the XML REST API for communicating with the switch.
"""

import logging
from lxml import etree
from os.path import dirname, join
import re
import requests
import schema

from hil.migrations import paths
from hil.model import db, Switch, SwitchSession
from hil.errors import BadArgumentError
from hil.model import BigIntegerType

paths[__name__] = join(dirname(__file__), 'migrations', 'brocade')

logger = logging.getLogger(__name__)


class Brocade(Switch, SwitchSession):
    """Brocade switch"""

    api_name = 'http://schema.massopencloud.org/haas/v0/switches/brocade'

    __mapper_args__ = {
        'polymorphic_identity': api_name,
    }

    id = db.Column(BigIntegerType,
                   db.ForeignKey('switch.id'), primary_key=True)
    hostname = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    interface_type = db.Column(db.String, nullable=False)

    @staticmethod
    def validate(kwargs):
        schema.Schema({
            'hostname': basestring,
            'username': basestring,
            'password': basestring,
            'interface_type': basestring,
        }).validate(kwargs)

    def session(self):
        return self

    @staticmethod
    def validate_port_name(port):
        """Valid port names for this switch are of the form 1/0/1 or 1/2"""

        val = re.compile(r'^\d+/\d+(/\d+)?$')
        if not val.match(port):
            raise BadArgumentError("Invalid port name. Valid port names for "
                                   "this switch are of the from 1/0/1 or 1/2")
        return

    def get_capabilities(self):
        return []

    def disconnect(self):
        pass

    def modify_port(self, port, channel, new_network):
        # XXX: We ought to be able to do a Port.query ... one() here, but
        # there's somthing I(zenhack)  don't understand going on with when
        # things are committed in the tests for this driver, and we don't
        # get any results that way. We should figure out what's going on with
        # that test and change this.
        (port,) = filter(lambda p: p.label == port, self.ports)
        interface = port.label

        if channel == 'vlan/native':
            if new_network is None:
                self._remove_native_vlan(interface)
            else:
                self._set_native_vlan(interface, new_network)
        else:
            match = re.match(re.compile(r'vlan/(\d+)'), channel)
            assert match is not None, "HIL passed an invalid channel to the" \
                " switch!"
            vlan_id = match.groups()[0]

            if new_network is None:
                self._remove_vlan_from_trunk(interface, vlan_id)
            else:
                assert new_network == vlan_id
                self._add_vlan_to_trunk(interface, vlan_id)

    def revert_port(self, port):
        self._remove_all_vlans_from_trunk(port)
        if self._get_native_vlan(port) is not None:
            self._remove_native_vlan(port)

    def get_port_networks(self, ports):
        """Get port configurations of the switch.

        Args:
            ports: List of ports to get the configuration for.

        Returns: Dictionary containing the configuration of the form:
        {
            Port<"port-3">: [("vlan/native", "23"), ("vlan/52", "52")],
            Port<"port-7">: [("vlan/23", "23")],
            Port<"port-8">: [("vlan/native", "52")],
            ...
        }

        """
        response = {}
        for port in ports:
            response[port] = filter(None,
                                    [self._get_native_vlan(port.label)]) \
                                    + self._get_vlans(port.label)
        return response

    def _get_mode(self, interface):
        """ Return the mode of an interface.

        Args:
            interface: interface to return the mode of

        Returns: 'access' or 'trunk'

        Raises: AssertionError if mode is invalid.

        """
        url = self._construct_url(interface, suffix='mode')
        response = self._make_request('GET', url)
        root = etree.fromstring(response.text)
        mode = root.find(self._construct_tag('vlan-mode')).text
        return mode

    def _enable_and_set_mode(self, interface, mode):
        """ Enables switching and sets the mode of an interface.

        Args:
            interface: interface to set the mode of
            mode: 'access' or 'trunk'

        Raises: AssertionError if mode is invalid.

        """
        # Enable switching
        url = self._construct_url(interface)
        payload = '<switchport></switchport>'
        self._make_request('POST', url, data=payload,
                           acceptable_error_codes=(409,))

        # Set the interface mode
        if mode in ['access', 'trunk']:
            url = self._construct_url(interface, suffix='mode')
            payload = '<mode><vlan-mode>%s</vlan-mode></mode>' % mode
            self._make_request('PUT', url, data=payload)
        else:
            raise AssertionError('Invalid mode')

    def _get_vlans(self, interface):
        """ Return the vlans of a trunk port.

        Does not include the native vlan. Use _get_native_vlan.

        Args:
            interface: interface to return the vlans of

        Returns: List containing the vlans of the form:
        [('vlan/vlan1', vlan1), ('vlan/vlan2', vlan2)]
        """
        try:
            url = self._construct_url(interface, suffix='trunk')
            response = self._make_request('GET', url)
            root = etree.fromstring(response.text)
            vlans = root.\
                find(self._construct_tag('allowed')).\
                find(self._construct_tag('vlan')).\
                find(self._construct_tag('add')).text
            return [('vlan/%s' % x, x) for x in vlans.split(',')]
        except AttributeError:
            return []

    def _get_native_vlan(self, interface):
        """ Return the native vlan of an interface.

        Args:
            interface: interface to return the native vlan of

        Returns: Tuple of the form ('vlan/native', vlan) or None
        """
        try:
            url = self._construct_url(interface, suffix='trunk')
            response = self._make_request('GET', url)
            root = etree.fromstring(response.text)
            vlan = root.find(self._construct_tag('native-vlan')).text
            return ('vlan/native', vlan)
        except AttributeError:
            return None

    def _add_vlan_to_trunk(self, interface, vlan):
        """ Add a vlan to a trunk port.

        If the port is not trunked, its mode will be set to trunk.

        Args:
            interface: interface to add the vlan to
            vlan: vlan to add
        """
        self._enable_and_set_mode(interface, 'trunk')
        url = self._construct_url(interface, suffix='trunk/allowed/vlan')
        payload = '<vlan><add>%s</vlan></vlan>' % vlan
        self._make_request('PUT', url, data=payload)

    def _remove_vlan_from_trunk(self, interface, vlan):
        """ Remove a vlan from a trunk port.

        Args:
            interface: interface to remove the vlan from
            vlan: vlan to remove
        """
        url = self._construct_url(interface, suffix='trunk/allowed/vlan')
        payload = '<vlan><remove>%s</remove></vlan>' % vlan
        self._make_request('PUT', url, data=payload)

    def _remove_all_vlans_from_trunk(self, interface):
        """ Remove all vlan from a trunk port.

        Args:
            interface: interface to remove the vlan from
        """
        url = self._construct_url(interface, suffix='trunk/allowed/vlan')
        payload = '<vlan><none>true</none></vlan>'
        requests.put(url, data=payload, auth=self._auth)

    def _set_native_vlan(self, interface, vlan):
        """ Set the native vlan of an interface.

        Args:
            interface: interface to set the native vlan to
            vlan: vlan to set as the native vlan
        """
        self._enable_and_set_mode(interface, 'trunk')
        self._disable_native_tag(interface)
        url = self._construct_url(interface, suffix='trunk')
        payload = '<trunk><native-vlan>%s</native-vlan></trunk>' % vlan
        self._make_request('PUT', url, data=payload)

    def _remove_native_vlan(self, interface):
        """ Remove the native vlan from an interface.

        Args:
            interface: interface to remove the native vlan from
        """
        url = self._construct_url(interface, suffix='trunk/native-vlan')
        self._make_request('DELETE', url)

    def _disable_native_tag(self, interface):
        """ Disable tagging of the native vlan

        Args:
            interface: interface to disable the native vlan tagging of

        """
        url = self._construct_url(interface, suffix='trunk/tag/native-vlan')
        self._make_request('DELETE', url, acceptable_error_codes=(404,))

    def _construct_url(self, interface, suffix=''):
        """ Construct the API url for a specific interface appending suffix.

        Args:
            interface: interface to construct the url for
            suffix: suffix to append at the end of the url

        Returns: string with the url for a specific interface and operation
        """
        # %22 is the encoding for double quotes (") in urls.
        # % escapes the % character.
        # Double quotes are necessary in the url because switch ports contain
        # forward slashes (/), ex. 101/0/10 is encoded as "101/0/10".
        return '%(hostname)s/rest/config/running/interface/' \
            '%(interface_type)s/%%22%(interface)s%%22%(suffix)s' \
            % {
                  'hostname': self.hostname,
                  'interface_type': self.interface_type,
                  'interface': interface,
                  'suffix': '/switchport/%s' % suffix if suffix else ''
            }

    @property
    def _auth(self):
        return self.username, self.password

    @staticmethod
    def _construct_tag(name):
        """ Construct the xml tag by prepending the brocade tag prefix. """
        return '{urn:brocade.com:mgmt:brocade-interface}%s' % name

    def _make_request(self, method, url, data=None,
                      acceptable_error_codes=()):
        r = requests.request(method, url, data=data, auth=self._auth)
        if r.status_code >= 400 and \
           r.status_code not in acceptable_error_codes:
            logger.error('Bad Request to switch. Response: %s', r.text)
        return r
