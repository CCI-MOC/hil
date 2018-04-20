"""Common functionality for switches that aren't session oriented and have
an API to talk to"""

import logging
import re
import requests

from hil.errors import SwitchError
from hil.model import SwitchSession
from hil.network_allocator import get_network_allocator

_CHANNEL_RE = re.compile(r'vlan/(\d+)')
logger = logging.getLogger(__name__)


class Session(SwitchSession):
    """Common base class for sessions in switches that are using an API"""

    def modify_port(self, port, channel, new_network):
        """This implements modify port that vlan centric switches can use"""
        if channel == 'vlan/native':
            if new_network is None:
                self._remove_native_vlan(port)
                self._port_shutdown(port)
            else:
                self._set_native_vlan(port, new_network)

        else:
            match = re.match(r'vlan/(\d+)', channel)
            assert match is not None, "Malformed channel: No VLAN ID found"
            vlan_id = match.groups()[0]
            legal = get_network_allocator(). \
                is_legal_channel_for(channel, vlan_id)
            assert legal, "Invalid VLAN ID"

            if new_network is None:
                self._remove_vlan_from_trunk(port, vlan_id)
            else:
                assert new_network == vlan_id
                self._add_vlan_to_trunk(port, vlan_id)

    def revert_port(self, port):
        self._remove_all_vlans_from_trunk(port)
        if self._get_native_vlan(port) is not None:
            self._remove_native_vlan(port)
        self._port_shutdown(port)

    def disconnect(self):
        pass

    def get_port_networks(self, ports):
        response = {}
        for port in ports:
            native = self._get_native_vlan(port.label)
            if native is not None:
                response[port] = [native]
            else:
                response[port] = []
            response[port] += self._get_vlans(port.label)
        return response

    def _make_request(self, method, url, data=None,
                      acceptable_error_codes=()):
        """This can make the http request for you.
        Also accetps a list of acceptable error codes if you need."""

        r = requests.request(method, url, data=data, auth=self._auth)
        if r.status_code >= 400 and \
           r.status_code not in acceptable_error_codes:
            logger.error('Bad Request to switch. '
                         'Response: %s and '
                         'Reason: %s', r.text, r.reason)
            raise SwitchError('Bad Request to switch. '
                              'Response: %s and '
                              'Reason: %s', r.text, r.reason)
        return r

    @property
    def _auth(self):
        return self.username, self.password

    def _remove_native_vlan(self, interface):
        assert False

    def _port_shutdown(self, interface):
        assert False

    def _set_native_vlan(self, interface, vlan):
        assert False

    def _remove_vlan_from_trunk(self, interface, vlan):
        assert False

    def _add_vlan_to_trunk(self, interface, vlan):
        assert False

    def _remove_all_vlans_from_trunk(self, interface):
        assert False

    def _get_native_vlan(self, interface):
        assert False

    def _get_vlans(self, interface):
        assert False
