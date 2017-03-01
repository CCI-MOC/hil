import json
from haas.client.base import ClientBase
from haas.client import errors


class Node(ClientBase):
    """Consists of calls to query and manipulate node related

    objects and relations.
    """

    def list(self, is_free):
        """List all nodes that HIL manages """
        url = self.object_url('nodes', is_free)
        return self.check_response(self.s.get(url))

    def show(self, node_name):
        """Shows attributes of a given node """

        url = self.object_url('node', node_name)
        return self.check_response(self.s.get(url))

    def register(self, node, subtype, *args):
        """Register a node with appropriate OBM driver. """
#       Registering a node requires apriori knowledge of the
#       available OBM driver and its corresponding arguments.
#       We assume that the HIL administrator is aware as to which
#       Node requires which OBM, and knows arguments required
#       for successful node registration.

        obm_api = "http://schema.massopencloud.org/haas/v0/obm/"
        obm_types = ["ipmi", "mock"]
#       FIXME: In future obm_types should be dynamically fetched
#        from haas.cfg, need a new api call for querying available
#        and currently active drivers for HIL
#        Not implemented yet.

    def delete(self, node_name):
        """Deletes the node from database. """
        url = self.object_url('node', node_name)
        return check_response(self.s.delete(url))

    def power_cycle(self, node_name):
        """Power cycles the <node> """
        url = self.object_url('node', node_name, 'power_cycle')
        return self.check_response(self.s.post(url))

    def power_off(self, node_name):
        """Power offs the <node> """
        url = self.object_url('node', node_name, 'power_off')
        return self.check_response(self.s.post(url))

    def add_nic(self, node_name, nic_name, macaddr):
        """Add a <nic> to <node>"""
        url = self.object_url('node', node_name, 'nic', nic_name)
        payload = json.dumps({'macaddr': macaddr})
        return self.check_response(self.s.put(url, data=payload))

    def remove_nic(self, node_name, nic_name):
        """Remove a <nic> from <node>"""
        url = self.object_url('node', node_name, 'nic', nic_name)
        return self.check_response(self.s.delete(url))

    def connect_network(self, node, nic, network, channel):
        """Connect <node> to <network> on given <nic> and <channel>"""
        url = self.object_url(
                'node', node, 'nic', nic, 'connect_network'
                )
        payload = json.dumps({
            'network': network, 'channel': channel
            })
        return self.check_response(self.s.post(url, payload))

    def detach_network(self, node, nic, network):
        """Disconnect <node> from <network> on the given <nic>. """
        url = self.object_url(
                'node', node, 'nic', nic, 'detach_network'
                )
        payload = json.dumps({'network': network})
        return self.check_response(self.s.post(url, payload))

    def show_console(self, node):
        """Display console log for <node> """
        # Not implemented yet.

    def start_console(self, node):
        """Start logging console output from <node> """
        url = self.object_url('node', node, 'console')
        return self.check_response(self.s.put(url))

    def stop_console(self, node):
        """Stop logging console output from <node> and delete the log"""
        url = self.object_url('node', node, 'console')
        return self.check_response(self.s.delete(url))
