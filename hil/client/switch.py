"""Client support for switch related api calls."""
import json
from hil.client.base import ClientBase
from hil.client.base import check_reserved_chars

SCHEMA = 'http://schema.massopencloud.org/haas/v0/switches/'
BROCADE = SCHEMA + 'brocade'
POWERCONNECT_55XX = SCHEMA + 'powerconnect55xx'
NEXUS = SCHEMA + 'nexus'
DELL_NOS9 = SCHEMA + 'dellnos9'
DELL_N3000 = SCHEMA + 'delln3000'
MOCK = SCHEMA + 'mock'

known_types = {
    NEXUS: Schema({
        'hostname': basestring,
        'username': basestring,
        'password': basestring,
        'dummy_vlan': basestring,
    }),
    DELL_N3000: Schema({
        'hostname': basestring,
        'username': basestring,
        'password': basestring,
        'dummy_vlan': basestring,
    }),
    DELL_NOS9: Schema({
        'hostname': basestring,
        'username': basestring,
        'password': basestring,
        'interface_type': basestring,
    }),
    BROCADE: Schema({
        'hostname': basestring,
        'username': basestring,
        'password': basestring,
        'interface_type': basestring,
    }),
    POWERCONNECT_55XX: Schema({
        'hostname': basestring,
        'username': basestring,
        'password': basestring,
    }),
    MOCK: Schema({
        'hostname': basestring,
        'username': basestring,
        'password': basestring,
    }),
}


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
        global SCHEMA
        switch_api = SCHEMA + subtype
        if switch_api in known_types:
            try:
                known_types[switch_api].validate(args)
            except Exception as e:
                SchemaError("Bad Request " + e)

        if subtype == "nexus" or subtype == "delln3000":
            switchinfo = {
                "type": switch_api,
                "hostname": args[0],
                "username": args[1],
                "password": args[2],
                "dummy_vlan": args[3]}
        elif subtype == "mock":
            switchinfo = {"type": switch_api,
                          "hostname": args[0],
                          "username": args[1], "password": args[2]}
        elif subtype == "powerconnect55xx":
            switchinfo = {"type": switch_api,
                          "hostname": args[0],
                          "username": args[1], "password": args[2]}
        elif subtype == "brocade" or "dellnos9":
            swtchinfo = {"type": switch_api,
                         "hostname": args[0],
                         "username": args[1], "password": args[2],
                         "interface_type": args[3]}
        else:
            raise Exception('ERROR: Invalid subtype supplied')

        url = self.object_url('switch', switch)
        payload = json.dumps(switchinfo)
        return self.check_response(
                self.httpClient.request("PUT", url, data=payload)
                )

    @check_reserved_chars()
    def delete(self, switch):
        """Deletes the switch named <switch>."""
        url = self.object_url('switch', switch)
        return self.check_response(self.httpClient.request("DELETE", url))

    @check_reserved_chars()
    def show(self, switch):
        """Shows attributes of <switch>. """
        url = self.object_url('switch', switch)
        return self.check_response(self.httpClient.request("GET", url))


class Port(ClientBase):
    """Port related operations. """

    @check_reserved_chars(slashes_ok=['port'])
    def register(self, switch, port):
        """Register a <port> with <switch>. """
        url = self.object_url('switch', switch, 'port', port)
        return self.check_response(self.httpClient.request("PUT", url))

    @check_reserved_chars(slashes_ok=['port'])
    def delete(self, switch, port):
        """Deletes information of the <port> for <switch> """
        url = self.object_url('switch', switch, 'port', port)
        return self.check_response(self.httpClient.request("DELETE", url))

    @check_reserved_chars(slashes_ok=['port'])
    def connect_nic(self, switch, port, node, nic):
        """Connects <port> of <switch> to <nic> of <node>. """
        url = self.object_url('switch', switch, 'port', port, 'connect_nic')
        payload = json.dumps({'node': node, 'nic': nic})
        return self.check_response(
                self.httpClient.request("POST", url, data=payload)
                )

    @check_reserved_chars(slashes_ok=['port'])
    def detach_nic(self, switch, port):
        """"Detaches <port> of <switch>. """
        url = self.object_url('switch', switch, 'port', port, 'detach_nic')
        return self.check_response(self.httpClient.request("POST", url))

    @check_reserved_chars(slashes_ok=['port'])
    def show(self, switch, port):
        """Show what's connected to <port>"""
        url = self.object_url('switch', switch, 'port', port)
        return self.check_response(self.httpClient.request("GET", url))

    @check_reserved_chars(slashes_ok=['port'])
    def port_revert(self, switch, port):
        """removes all vlans from a switch port"""
        url = self.object_url('switch', switch, 'port', port, 'revert')
        return self.check_response(self.httpClient.request("POST", url))
