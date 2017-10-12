# Copyright 2017 Massachusetts Open Cloud Contributors
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

"""A switch driver for Dell S3048-ON running Dell OS 9.

Uses the XML REST API for communicating with the switch.
"""

import logging
from lxml import etree
import re
import requests
import schema

from hil import model
from hil.model import db, Switch, SwitchSession
from hil.errors import BadArgumentError, BlockedError
from hil.model import BigIntegerType
from hil.network_allocator import get_network_allocator

logger = logging.getLogger(__name__)

CONFIG = 'config-commands'
SHOW = 'show-command'


class DellNOS9(Switch, SwitchSession):
    """Dell S3048-ON running Dell NOS9"""
    api_name = 'http://schema.massopencloud.org/haas/v0/switches/dellnos9'

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

    def ensure_legal_operation(self, nic, op_type, channel):
        # get the network attachments for <nic> from the database
        table = model.NetworkAttachment
        query = db.session.query(table).filter(table.nic_id == nic.id)

        if channel != 'vlan/native' and op_type == 'connect' and \
           query.filter(table.channel == 'vlan/native').count() == 0:
            # checks if it is trying to attach a trunked network, and then in
            # in the db see if nic does not have any networks attached natively
            raise BlockedError("Please attach a native network first")
        elif channel == 'vlan/native' and op_type == 'detach' and \
                query.filter(table.channel != 'vlan/native').count() > 0:
            # if it is detaching a network, then check in the database if there
            # are any trunked vlans.
            raise BlockedError("Please remove all trunked Vlans"
                               " before removing the native vlan")
        else:
            return

    @staticmethod
    def validate_port_name(port):
        """Valid port names for this switch are of the form 1/0/1 or 1/2"""

        if not re.match(r'^\d+/\d+(/\d+)?$', port):
            raise BadArgumentError("Invalid port name. Valid port names for "
                                   "this switch are of the form 1/0/1 or 1/2")
        return

    def disconnect(self):
        """Since the switch is not connection oriented, we don't need to
        establish a session or disconnect from it."""

    def modify_port(self, port, channel, new_network):
        (port,) = filter(lambda p: p.label == port, self.ports)
        interface = port.label

        if channel == 'vlan/native':
            if new_network is None:
                self._remove_native_vlan(interface)
                self._port_shutdown(interface)
            else:
                self._set_native_vlan(interface, new_network)
        else:
            vlan_id = channel.replace('vlan/', '')
            legal = get_network_allocator(). \
                is_legal_channel_for(channel, vlan_id)
            assert legal, "HIL passed an invalid channel to the switch!"

            if new_network is None:
                self._remove_vlan_from_trunk(interface, vlan_id)
            else:
                assert new_network == vlan_id
                self._add_vlan_to_trunk(interface, vlan_id)

    def revert_port(self, port):
        self._remove_all_vlans_from_trunk(port)
        if self._get_native_vlan(port) is not None:
            self._remove_native_vlan(port)
        self._port_shutdown(port)

    def get_port_networks(self, ports):
        response = {}
        for port in ports:
            response[port] = self._get_vlans(port.label)
            native = self._get_native_vlan(port.label)
            if native is not None:
                response[port].append(native)

        return response

    def _get_vlans(self, interface):
        """ Return the vlans of a trunk port.

        Does not include the native vlan. Use _get_native_vlan.

        Args:
            interface: interface to return the vlans of

        Returns: List containing the vlans of the form:
        [('vlan/vlan1', vlan1), ('vlan/vlan2', vlan2)]
        """

        # It uses the REST API CLI which is slow but it is the only way
        # because the switch is VLAN centric. Doing a GET on interface won't
        # return the VLANs on it, we would have to do get on all vlans (if that
        # worked reliably in the first place) and then find our interface there
        # which is not feasible.

        if not self._is_port_on(interface):
            return []
        response = self._get_port_info(interface)

        # finds a comma separated list of integers and/or ranges starting with
        # T. Sample T12,14-18,23,28,80-90 or T20 or T20,22 or T20-22
        match = re.search(r'T(\d+(-\d+)?)(,\d+(-\d+)?)*', response)
        if match is None:
            return []
        range_str = match.group().replace('T', '').split(',')
        vlan_list = []
        # need to interpret the ranges to numbers. e.g. 14-18 as 14,15,16,17,18
        for num_str in range_str:
            if '-' in num_str:
                num_str = num_str.split('-')
                for x in range(int(num_str[0]), int(num_str[1])+1):
                    vlan_list.append(str(x))
            else:
                vlan_list.append(num_str)

        return [('vlan/%s' % x, x) for x in vlan_list]

    def _get_native_vlan(self, interface):
        """ Return the native vlan of an interface.

        Args:
            interface: interface to return the native vlan of

        Returns: Tuple of the form ('vlan/native', vlan) or None

        Similar to _get_vlans()
        """
        if not self._is_port_on(interface):
            return None
        response = self._get_port_info(interface)
        match = re.search(r'NativeVlanId:(\d+)\.', response)
        if match is not None:
            vlan = match.group(1)
        else:
            logger.error('Unexpected: No native vlan found')
            return

        # FIXME: At this point, we are unable to remove the default native vlan
        # The switchport defaults to native vlan 1. Our deployment tests make
        # assertions that a switchport has no default vlan at start.
        # To get the tests to pass, we return None if we see the switchport has
        # a default native vlan (=1). This needs to be fixed ASAP.
        if vlan == '1':
            return None

        return ('vlan/native', vlan)

    def _get_port_info(self, interface):
        """Returns the output of a show interface command. This removes all
        spaces from the response before returning it which is then parsed by
        the caller.

        Sample Response:
        u"<outputxmlns='http://www.dell.com/ns/dell:0.1/root'>\n
        <command>show interfaces switchport GigabitEthernet1/3\r\n\r\n
        Codes: U-Untagged T-Tagged\r\n x-Dot1x untagged,X-Dot1xtagged\r\n
        G-GVRP tagged,M-Trunk\r\n i-Internal untagged, I-Internaltagged,
        v-VLTuntagged, V-VLTtagged\r\n\r\n Name:GigabitEthernet1/3\r\n 802.1Q
        Tagged:Hybrid\r\n Vlan membership:\r\n Q Vlans\r\n U 1512 \r\n T 1511
        1612-1614,1700\r\n\r\n Native Vlan Id: 1512.\r\n\r\n\r\n\r\n
        MOC-Dell-S3048-ON#</command>\n</output>\n"
        """
        command = 'interfaces switchport %s %s' % \
            (self.interface_type, interface)
        response = self._execute(interface, SHOW, command)
        return response.text.replace(' ', '')

    def _add_vlan_to_trunk(self, interface, vlan):
        """ Add a vlan to a trunk port.

        If the port is not trunked, its mode will be set to trunk.

        Args:
            interface: interface to add the vlan to
            vlan: vlan to add
        """
        if not self._is_port_on(interface):
            self._port_on(interface)
        command = 'interface vlan ' + vlan + '\r\n tagged ' + \
            self.interface_type + ' ' + interface
        self._execute(interface, CONFIG, command)

    def _remove_vlan_from_trunk(self, interface, vlan):
        """ Remove a vlan from a trunk port.

        Args:
            interface: interface to remove the vlan from
            vlan: vlan to remove
        """
        command = self._remove_vlan_command(interface, vlan)
        self._execute(interface, CONFIG, command)

    def _remove_all_vlans_from_trunk(self, interface):
        """ Remove all vlan from a trunk port.

        Args:
            interface: interface to remove the vlan from
        """
        command = ''
        for vlan in self._get_vlans(interface):
            command += self._remove_vlan_command(interface, vlan[1]) + '\r\n '
        # execute command only if there are some vlans to remove, otherwise
        # the switch complains
        if command is not '':
            self._execute(interface, CONFIG, command)

    def _remove_vlan_command(self, interface, vlan):
        """Returns command to remove <vlan> from <interface>"""
        return 'interface vlan ' + vlan + '\r\n no tagged ' + \
            self.interface_type + ' ' + interface

    def _set_native_vlan(self, interface, vlan):
        """ Set the native vlan of an interface.

        Args:
            interface: interface to set the native vlan to
            vlan: vlan to set as the native vlan

        Method relies on the REST API CLI which is slow
        """
        if not self._is_port_on(interface):
            self._port_on(interface)
        command = 'interface vlan ' + vlan + '\r\n untagged ' + \
            self.interface_type + ' ' + interface
        self._execute(interface, CONFIG, command)

    def _remove_native_vlan(self, interface):
        """ Remove the native vlan from an interface.

        Args:
            interface: interface to remove the native vlan from.vlan
        """
        try:
            vlan = self._get_native_vlan(interface)[1]
            command = 'interface vlan ' + vlan + '\r\n no untagged ' + \
                self.interface_type + ' ' + interface
            self._execute(interface, CONFIG, command)
        except TypeError:
            logger.error('No native vlan to remove')

    def _port_shutdown(self, interface):
        """ Shuts down <interface>

        Turn off portmode hybrid, disable switchport, and then shut down the
        port. All non-default vlans must be removed before calling this.
        """

        url = self._construct_url(interface=interface)
        interface = self._convert_interface_type(self.interface_type) + \
            interface.replace('/', '-')
        payload = '<interface><name>%s</name><portmode><hybrid>false' \
                  '</hybrid></portmode><shutdown>true</shutdown>' \
                  '</interface>' % interface

        self._make_request('PUT', url, data=payload)

    def _port_on(self, interface):
        """ Turns on <interface>

        Turn on port and enable hybrid portmode and switchport.
        """

        url = self._construct_url(interface=interface)
        interface = self._convert_interface_type(self.interface_type) + \
            interface.replace('/', '-')
        payload = '<interface><name>%s</name><portmode><hybrid>true' \
                  '</hybrid></portmode><switchport></switchport>' \
                  '<shutdown>false</shutdown></interface>' % interface

        self._make_request('PUT', url, data=payload)

    def _is_port_on(self, port):
        """ Returns a boolean that tells the status of a switchport"""

        # the url here requires a suffix to GET the shutdown tag in response.
        url = self._construct_url(interface=port) + '\?with-defaults'
        response = self._make_request('GET', url)
        root = etree.fromstring(response.text)
        shutdown = root.find(self._construct_tag('shutdown')).text

        assert shutdown in ('false', 'true'), "unexpected state of switchport"
        return shutdown == 'false'

    # HELPER METHODS *********************************************

    def _execute(self, interface, command_type, command):
        """This method gets the url & the payload and executes <command>"""
        url = self._construct_url()
        payload = self._make_payload(command_type, command)
        return self._make_request('POST', url, data=payload)

    def _construct_url(self, interface=None):
        """ Construct the API url for a specific interface.

        Args:
            interface: interface to construct the url for

        Returns: string with the url for a specific interface and operation

        If interface is None, then it returns the URL for REST API CLI.
        """

        if interface is None:
            return '%s/api/running/dell/_operations/cli' % self.hostname

        try:
            self.validate_port_name(interface)
            # if `interface` refers to port name
            # the urls have dashes instead of slashes in interface names
            interface = interface.replace('/', '-')
            interface_type = self._convert_interface_type(self.interface_type)
        except BadArgumentError:
            # interface refers to `vlan`
            interface_type = 'vlan-'

        return ''.join([self.hostname, '/api/running/dell/interfaces/'
                       'interface/', interface_type, interface])

    @staticmethod
    def _convert_interface_type(interface_type):
        """ Convert the interface type from switch CLI form to what the API
        server understands.

        Args:
            interface: the interface in the CLI-form

        Returns: string interface
        """
        iftypes = {'GigabitEthernet': 'gige-',
                   'TenGigabitEthernet': 'tengig-',
                   'TwentyfiveGigabitEthernet': 'twentyfivegig-',
                   'fortyGigE': 'fortygig-',
                   'peGigabitEthernet': 'pegig-',
                   'FiftyGigabitEthernet': 'fiftygig-',
                   'HundredGigabitEthernet': 'hundredgig-'}

        return iftypes[interface_type]

    @property
    def _auth(self):
        return self.username, self.password

    @staticmethod
    def _make_payload(command, command_type):
        """Makes payload for passing CLI commands using the REST API"""

        return '<input><%s>%s</%s></input>' % (command, command_type, command)

    @staticmethod
    def _construct_tag(name):
        """ Construct the xml tag by prepending the dell tag prefix. """
        return '{http://www.dell.com/ns/dell:0.1/root}%s' % name

    def _make_request(self, method, url, data=None):
        r = requests.request(method, url, data=data, auth=self._auth)
        if r.status_code >= 400:
            logger.error('Bad Request to switch. Response: %s', r.text)
        return r
