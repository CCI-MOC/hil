"""Client support for node related api calls."""
import json
from hil.client.base import ClientBase
from hil.client.base import check_reserved_chars


class Node(ClientBase):
    """Consists of calls to query and manipulate node related

    objects and relations.
    """

    def list(self, is_free):
        """List all nodes that HIL manages """
        url = self.object_url('nodes', is_free)
        return self.check_response(self.httpClient.request('GET', url))

    @check_reserved_chars('node')
    def show(self, node_name):
        """Shows attributes of a given node """
        url = self.object_url('node', node_name)
        return self.check_response(self.httpClient.request('GET', url))

    def register(self, node, subtype, *args):
        """Register a node with appropriate OBM driver. """
        # Registering a node requires apriori knowledge of the
        # available OBM driver and its corresponding arguments.
        # We assume that the HIL administrator is aware as to which
        # Node requires which OBM, and knows arguments required
        # for successful node registration.

        # FIXME: In future obm_types should be dynamically fetched.
        # We need a new api call for querying available
        # and currently active drivers for HIL
        # obm_api = "http://schema.massopencloud.org/haas/v0/obm/"
        # obm_types = ["ipmi", "mock"]
        raise NotImplementedError

    @check_reserved_chars('node')
    def delete(self, node_name):
        """Deletes the node from database. """
        url = self.object_url('node', node_name)
        return self.check_response(self.httpClient.request('DELETE', url))

    @check_reserved_chars('node')
    def power_cycle(self, node_name, force=False):
        """Power cycles the <node> """
        url = self.object_url('node', node_name, 'power_cycle')
        payload = json.dumps({'force': force})
        return self.check_response(
                self.httpClient.request('POST', url, data=payload)
                )

    @check_reserved_chars('node')
    def power_off(self, node_name):
        """Power offs the <node> """
        url = self.object_url('node', node_name, 'power_off')
        return self.check_response(self.httpClient.request('POST', url))

    @check_reserved_chars('node', 'nic')
    def add_nic(self, node_name, nic_name, macaddr):
        """Add a <nic> to <node>"""
        url = self.object_url('node', node_name, 'nic', nic_name)
        payload = json.dumps({'macaddr': macaddr})
        return self.check_response(
                self.httpClient.request('PUT', url, data=payload)
                )

    @check_reserved_chars('node', 'nic')
    def remove_nic(self, node_name, nic_name):
        """Remove a <nic> from <node>"""
        url = self.object_url('node', node_name, 'nic', nic_name)
        return self.check_response(self.httpClient.request('DELETE', url))

    @check_reserved_chars('node', 'nic', 'network', 'channel',
                          slashes_ok=['channel'])
    def connect_network(self, node, nic, network, channel):
        """Connect <node> to <network> on given <nic> and <channel>"""
        url = self.object_url(
                'node', node, 'nic', nic, 'connect_network'
                )
        payload = json.dumps({
            'network': network, 'channel': channel
            })
        return self.check_response(
                self.httpClient.request('POST', url, data=payload)
                )

    @check_reserved_chars('node', 'nic', 'network')
    def detach_network(self, node, nic, network):
        """Disconnect <node> from <network> on the given <nic>. """
        url = self.object_url(
                'node', node, 'nic', nic, 'detach_network'
                )
        payload = json.dumps({'network': network})
        return self.check_response(
                self.httpClient.request('POST', url, data=payload)
                )

    def show_console(self, node):
        """Display console log for <node> """
        raise NotImplementedError

    @check_reserved_chars('node')
    def start_console(self, node):
        """Start logging console output from <node> """
        url = self.object_url('node', node, 'console')
        return self.check_response(self.httpClient.request('PUT', url))

    @check_reserved_chars('node')
    def stop_console(self, node):
        """Stop logging console output from <node> and delete the log"""
        url = self.object_url('node', node, 'console')
        return self.check_response(self.httpClient.request('DELETE', url))
