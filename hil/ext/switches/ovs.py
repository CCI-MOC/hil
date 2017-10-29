
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
"""A switch driver for OpenVswitch.
"""

import re
import logging
import schema
import os
import ast
from commands import getstatusoutput

from hil.model import db, Switch, BigIntegerType, SwitchSession
from hil.migrations import paths
from os.path import dirname, join
logger = logging.getLogger(__name__)


class VlanError(Exception):
    """ Raise this exception when vlan cannot be added to the port."""


class PortInfoNotFound(Exception):
    """ Raise this exception when this driver is unable to fetch
    information for a given port.
    """


class OVS_RequestFailed(Exception):
    """ Raise this exception when a requestOVS failure
    does not follow into any of the above exceptions.
    """


class Ovs(Switch, SwitchSession):
    """ Driver for openvswitch. """
    api_name = 'http://schema.massopencloud.org/haas/v0/switches/ovs'
    dir_name = os.path.dirname(__file__)
    __mapper_args__ = {
        'polymorphic_identity': api_name,
    }

    id = db.Column(
            BigIntegerType, db.ForeignKey('switch.id'), primary_key=True
            )
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
        """ required from superclass. """
        return self

    def disconnect(self):
        """ required from superclass. """

    @staticmethod
    def validate_port_name(port):
        """ This driver accepts any string as port name."""

    def str2list(self, a_string):
        """ Converts a string representation of list to list.
        Empty list is put as None.
        """
        if a_string[0] == '[' and a_string[1] == ']':
            return None
        else:
            a_string = a_string.replace("[", "['").replace("]", "']")
            a_string = a_string.replace(",", "','")
            a_list = ast.literal_eval(a_string)
            a_list = [ele.strip() for ele in a_list]
            return a_list

    def str2dict(self, a_string):
        """Converts a string representation of dictionary to a dictionary."""
        if a_string[0] == '{' and a_string[1] == '}':
            a_dict = ast.literal_eval(a_string)
            return a_dict
        elif a_string[0] == '{' and len(a_string) > 2:
            a_string = a_string.replace("{", "{'").replace("}", "'}")
            a_string = a_string.replace(":", "':'").replace(",", "','")
            a_dict = ast.literal_eval(a_string)
            a_dict = {k.strip(): v.strip() for k, v in a_dict.iteritems()}
            return a_dict
        else:
            return None

    def _requestOVS(self, ovs_statements, error):
        """ send ``payload`` to switch.
        If successful do nothing else raise exception as ``error``.
        """
        payload = (
                'echo {x} |sudo -S bash -c "'.format(x=self.password) +
                ovs_statements + '"'
                )
        result = getstatusoutput(payload)
        if (result[0] != 0):
            raise error(result[1])
        else:
            return None

    def _interface_info(self, port):
        """Fetches latest committed configuration information about `port`"""
        ovs = self._create_session()
        a = getstatusoutput(ovs + " list port {port}".format(port=port))
        if (a[0] > 0):
            raise PortInfoNotFound(a[1])
        else:
            a = a[1].split('\n')

        rem_info = "[sudo] password for " + self.username + ": "
        a[0] = a[0].replace(rem_info, '')
        i_info = dict(s.split(':') for s in a)
        i_info = {k.strip(): v.strip() for k, v in i_info.iteritems()}
        for x in i_info.keys():
            if i_info[x][0] in ["{", "["]:
                i_info[x] = \
                        self.str2list(i_info[x]) or self.str2dict(i_info[x])

        return i_info

    def revert_port(self, port):
        """Resets the port to the factory default.
        """
        payload = (
                'ovs-vsctl del-port {port}; \
                        ovs-vsctl add-port {switch} {port}'.format(
                    switch=self.hostname, port=port
                    ) + ' vlan_mode=native-untagged'
                )
        return self._requestOVS(payload, OVS_RequestFailed)

    def modify_port(self, port, channel, network_id):
        """ Changes vlan assignment to the port.
        `node_connect_network` with 'vlan/native' flag:
        enable port; set port to trunk mode; assign native_vlan;
        remove default vlan
        """
        (port,) = filter(lambda p: p.label == port, self.ports)
        interface = port.label

        if channel == 'vlan/native':
            if network_id is None:
                self._remove_native_vlan(interface)
            else:
                self._set_native_vlan(interface, network_id)
        else:
            match = re.match(re.compile(r'vlan/(\d+)'), channel)
            assert match is not None, "HIL passed an invalid channel to the" \
                " switch!"
            vlan_id = match.groups()[0]

            if network_id is None:
                self._remove_vlan_from_port(interface, vlan_id)
            else:
                assert network_id == vlan_id
                try:
                    self._add_vlan_to_trunk(interface, vlan_id)
                except VlanError as e:
                    return e

    def get_port_networks(self, ports):
        """ Get port configurations of the switch.
        This is an important function for deployment tests.

        Args:
            ports: List of sqlalchemy objects representing ports.

        Returns: Dictionary containing the configuration of the form:
        Make sure the output looks equivalent to the one in the example.

        {
            <hil.model.Port object at 0x7f00ca35f950>:
            [("vlan/native", "23"), ("vlan/52", "52")],
            <hil.model.Port object at 0x7f00cb64fcd0>: [("vlan/23", "23")],
            <hil.model.Port object at 0x7f00cabcd100>: [("vlan/native", "52")],
            ...
        }
        """
        raise NotImplemented

    def _set_native_vlan(self, port, network_id):
        """Sets native vlan for a trunked port.
        It enables the port, if it is the first vlan for the port.
        """
        payload = (
                " ovs-vsctl set port {port} tag={netid}".format(
                        port=port, netid=network_id
                        ) + " vlan_mode=native-untagged"
                    )

        return self._requestOVS(payload, VlanError)

    def _remove_native_vlan(self, port):
        """Removes native vlan from a trunked port.
        If it is the last vlan to be removed, it disables the port and
        reverts its state to default configuration
        """
        port_info = self._interface_info(port)
        vlan_id = port_info['tag']
        payload = " ovs-vsctl remove port {port} tag {vlan_id}".format(
                    port=port, vlan_id=vlan_id
                    )
        return self._requestOVS(payload, VlanError)

    def _add_vlan_to_trunk(self, port, vlan_id):
        """ Adds vlans to a trunk port. """
        port_info = self._interface_info(port)

        if port_info['trunks'] is None:
            payload = " ovs-vsctl set port {port} trunks={vlan_id}".format(
                    port=port, vlan_id=vlan_id
                    )
        else:
            all_trunks = ','.join(port_info['trunks'])+','+vlan_id
            payload = " ovs-vsctl set port {port} trunks={vlan_id}".format(
                        port=port, vlan_id=all_trunks
                        )

        return self._requestOVS(payload, VlanError)

    def _remove_vlan_from_port(self, port, vlan_id):
        """ removes a single vlan specified by `vlan_id` """
        port_info = self._interface_info(port)

        if port_info['trunks'] is not None:
            payload = " ovs-vsctl remove port {port} trunks {vlan_id}".format(
                        port=port, vlan_id=vlan_id
                        )
        return self._requestOVS(payload, VlanError)
