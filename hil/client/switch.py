"""Client support for switch related api calls."""
import json
from hil.client.base import ClientBase


class Switch(ClientBase):
    """Consists of calls to query and manipulate node related

    objects and relations.
    """

    def list(self):
        """List all nodes that HIL manages """
        url = self.object_url('/switches')
        return self.check_response(self.httpClient.request("GET", url))

    def register(self, switch, subtype, *args):
        """Registers a switch with name <switch> and
        model <subtype> , and relevant arguments  in <*args>
        """
#       It is assumed that the HIL administrator is aware of
#       of the switches HIL will control and has read the
#       HIL documentation to use appropriate flags to register
#       it with HIL.
        raise NotImplementedError

    def delete(self, switch):
        """Deletes the switch named <switch>."""
        url = self.object_url('switch', switch)
        return self.check_response(self.httpClient.request("DELETE", url))

    def show(self, switch):
        """Shows attributes of <switch>. """
        url = self.object_url('switch', switch)
        return self.check_response(self.httpClient.request("GET", url))


class Port(ClientBase):
    """Port related operations. """

    def register(self, switch, port):
        """Register a <port> with <switch>. """
        url = self.object_url('switch', switch, 'port', port)
        return self.check_response(self.httpClient.request("PUT", url))

    def delete(self, switch, port):
        """Deletes information of the <port> for <switch> """
        url = self.object_url('switch', switch, 'port', port)
        return self.check_response(self.httpClient.request("DELETE", url))

    def connect_nic(self, switch, port, node, nic):
        """Connects <port> of <switch> to <nic> of <node>. """
        url = self.object_url('switch', switch, 'port', port, 'connect_nic')
        payload = json.dumps({'node': node, 'nic': nic})
        return self.check_response(
                self.httpClient.request("POST", url, data=payload)
                )

    def detach_nic(self, switch, port):
        """"Detaches <port> of <switch>. """
        url = self.object_url('switch', switch, 'port', port, 'detach_nic')
        return self.check_response(self.httpClient.request("POST", url))

    def show(self, switch, port):
        """Show what's connected to <port>"""
        url = self.object_url('switch', switch, 'port', port)
        return self.check_response(self.httpClient.request("GET", url))

    def port_revert(self, switch, port):
        """removes all vlans from a switch port"""
        url = self.object_url('switch', switch, 'port', port, 'revert')
        return self.check_response(self.httpClient.request("POST", url))
