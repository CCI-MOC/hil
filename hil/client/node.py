"""Client support for node related api calls."""
import json
from hil.client.base import ClientBase


class Node(ClientBase):
    """Consists of calls to query and manipulate node related

    objects and relations.
    """

    def list(self, is_free):
        """List all nodes that HIL manages """
        url = self.object_url('nodes', is_free)
        return self.check_response(self.httpClient.request('GET', url))

    def show(self, node_name):
        """Shows attributes of a given node """
        self.check_reserved('node', node_name)
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

    def delete(self, node_name):
        """Deletes the node from database. """
        self.check_reserved('node', node_name)
        url = self.object_url('node', node_name)
        return self.check_response(self.httpClient.request('DELETE', url))

    def power_cycle(self, node_name, force=False):
        """Power cycles the <node> """
        self.check_reserved('node', node_name)
        url = self.object_url('node', node_name, 'power_cycle')
        payload = json.dumps({'force': force})
        return self.check_response(
                self.httpClient.request('POST', url, data=payload)
                )

    def power_off(self, node_name):
        """Power offs the <node> """
        self.check_reserved('node', node_name)
        url = self.object_url('node', node_name, 'power_off')
        return self.check_response(self.httpClient.request('POST', url))

    def add_nic(self, node_name, nic_name, macaddr):
        """Add a <nic> to <node>"""
        self.check_reserved('node', node_name)
        self.check_reserved('nic', nic_name)
        url = self.object_url('node', node_name, 'nic', nic_name)
        payload = json.dumps({'macaddr': macaddr})
        return self.check_response(
                self.httpClient.request('PUT', url, data=payload)
                )

    def remove_nic(self, node_name, nic_name):
        """Remove a <nic> from <node>"""
        self.check_reserved('node', node_name)
        self.check_reserved('nic', nic_name)
        url = self.object_url('node', node_name, 'nic', nic_name)
        return self.check_response(self.httpClient.request('DELETE', url))

    def connect_network(self, node, nic, network, channel):
        """Connect <node> to <network> on given <nic> and <channel>"""
        self.check_reserved('node', node)
        self.check_reserved('nic', nic)
        self.check_reserved('network', network)
        self.check_reserved('channel', channel, slashes_ok=True)
        url = self.object_url(
                'node', node, 'nic', nic, 'connect_network'
                )
        payload = json.dumps({
            'network': network, 'channel': channel
            })
        return self.check_response(
                self.httpClient.request('POST', url, data=payload)
                )

    def detach_network(self, node, nic, network):
        """Disconnect <node> from <network> on the given <nic>. """
        self.check_reserved('node', node)
        self.check_reserved('nic', nic)
        self.check_reserved('network', network)
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

    def start_console(self, node):
        """Start logging console output from <node> """
        self.check_reserved('node', node)
        url = self.object_url('node', node, 'console')
        return self.check_response(self.httpClient.request('PUT', url))

    def stop_console(self, node):
        """Stop logging console output from <node> and delete the log"""
        self.check_reserved('node', node)
        url = self.object_url('node', node, 'console')
        return self.check_response(self.httpClient.request('DELETE', url))
