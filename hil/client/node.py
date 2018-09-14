"""Client support for node related api calls."""
import json
from hil.client.base import ClientBase, FailedAPICallException
from hil.client.base import check_reserved_chars


class Node(ClientBase):
    """Consists of calls to query and manipulate node related

    objects and relations.
    """

    def list(self, is_free):
        """List all nodes that HIL manages """
        url = self.object_url('nodes', is_free)
        return self.check_response(self.httpClient.request('GET', url))

    @check_reserved_chars()
    def show(self, node_name):
        """Shows attributes of a given node """
        url = self.object_url('node', node_name)
        return self.check_response(self.httpClient.request('GET', url))

    @check_reserved_chars(dont_check=['obmd_uri'])
    def register(self, node, obmd_uri, obmd_admin_token):
        """Register a node. """
        url = self.object_url('node', node)
        payload = json.dumps({
            "obmd": {
                'uri': obmd_uri,
                'admin_token': obmd_admin_token,
            },
        })
        return self.check_response(
                self.httpClient.request('PUT', url, data=payload)
                )

    @check_reserved_chars()
    def delete(self, node_name):
        """Deletes the node from database. """
        url = self.object_url('node', node_name)
        return self.check_response(self.httpClient.request('DELETE', url))

    @check_reserved_chars()
    def enable_obm(self, node_name):
        """Enables the node's obm."""
        url = self.object_url('node', node_name, 'obm')
        return self.check_response(
            self.httpClient.request('PUT', url, data=json.dumps({
                'enabled': True,
            }))
        )

    @check_reserved_chars()
    def disable_obm(self, node_name):
        """Disables the node's obm."""
        url = self.object_url('node', node_name, 'obm')
        return self.check_response(
            self.httpClient.request('PUT', url, data=json.dumps({
                'enabled': False,
            })))

    @check_reserved_chars(dont_check=['force'])
    def power_cycle(self, node_name, force=False):
        """Power cycles the <node> """
        url = self.object_url('node', node_name, 'power_cycle')
        payload = json.dumps({'force': force})
        return self.check_response(
                self.httpClient.request('POST', url, data=payload)
                )

    @check_reserved_chars()
    def power_off(self, node_name):
        """Power offs the <node> """
        url = self.object_url('node', node_name, 'power_off')
        return self.check_response(self.httpClient.request('POST', url))

    @check_reserved_chars()
    def power_on(self, node_name):
        """Power ons the <node> """
        url = self.object_url('node', node_name, 'power_on')
        return self.check_response(self.httpClient.request('POST', url))

    @check_reserved_chars()
    def set_bootdev(self, node, dev):
        """Set <node> to boot from <dev> persistently"""
        url = self.object_url('node', node, 'boot_device')
        payload = json.dumps({'bootdev': dev})
        return self.check_response(
                self.httpClient.request('PUT', url, data=payload)
                )

    @check_reserved_chars(dont_check=['macaddr'])
    def add_nic(self, node_name, nic_name, macaddr):
        """Add a <nic> to <node>"""
        url = self.object_url('node', node_name, 'nic', nic_name)
        payload = json.dumps({'macaddr': macaddr})
        return self.check_response(
                self.httpClient.request('PUT', url, data=payload)
                )

    @check_reserved_chars()
    def remove_nic(self, node_name, nic_name):
        """Remove a <nic> from <node>"""
        url = self.object_url('node', node_name, 'nic', nic_name)
        return self.check_response(self.httpClient.request('DELETE', url))

    @check_reserved_chars(slashes_ok=['channel'])
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

    @check_reserved_chars()
    def detach_network(self, node, nic, network):
        """Disconnect <node> from <network> on the given <nic>. """
        url = self.object_url(
                'node', node, 'nic', nic, 'detach_network'
                )
        payload = json.dumps({'network': network})
        return self.check_response(
                self.httpClient.request('POST', url, data=payload)
                )

    @check_reserved_chars()
    def metadata_set(self, node, label, value):
        """Register metadata with <label> and <value> with <node>"""
        url = self.object_url('node', node, 'metadata', label)
        payload = json.dumps({'value': value})
        return self.check_response(
                self.httpClient.request('PUT', url, data=payload)
               )

    @check_reserved_chars()
    def metadata_delete(self, node, label):
        """Delete metadata with <label> from a <node>"""
        url = self.object_url('node', node, 'metadata', label)
        return self.check_response(self.httpClient.request('DELETE', url))

    @check_reserved_chars()
    def show_console(self, node):
        """Stream the console for <node>.

        Unlike most of the other API calls, rather than returning a json
        value, this returns an iterator allowing the caller to read the
        console in a streaming fashion. The iterator's next() method
        returns the next chunk of data from the console, when it is
        available.
        """
        url = self.object_url('node', node, 'console')
        response = self.httpClient.request('GET', url)
        # we don't call check_response here because we want to return the
        # raw byte stream, rather than reading the whole thing in and
        # converting it to json.
        if 200 <= response.status_code < 300:
            return response.body
        raise FailedAPICallException(error_type=response.status_code,
                                     message=response.content)

    def show_networking_action(self, status_id):
        """Returns the status of the networking action"""
        url = self.object_url('networking_action', status_id)
        return self.check_response(self.httpClient.request('GET', url))
