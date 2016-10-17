from haas.client.base import *
from haas.client.client_errors import *


class Node(ClientBase):
    """ Consists of calls to query and manipulate node related
    objects and relations """

    def list(self, is_free):
        """ List all nodes that HIL manages """
        url = self.object_url('nodes', is_free)
        q = requests.get(url, headers={"Authorization": "Basic %s" % self.auth})
        if q.ok:
            return q.json()
        elif q.status_code == 401:
            raise AuthenticationError("Make sure credentials match chosen authentication backend.")

    def show_node(self, node_name):
        """ Shows attributes of a given node """

        self.node_name = node_name
        url = self.object_url('node', node_name)
        q = requests.get(url, headers={"Authorization": "Basic %s" %self.auth})
        return q.json()

    def delete(self, node_name):
        """ Deletes the node from database. """
        self.node_name = node_name
        url = self.object_url('node', node_name)
        q = requests.delete(url, headers={"Authorization": "Basic %s" %self.auth})
        if q.ok:
            return
        elif q.status_code == 409:
            raise BlockedError("Make sure all nics are removed before deleting the node")
        elif q.status_code == 404:
            raise NotFoundError("No such node exist. Nothing to delete.")

    def power_cycle(self, node_name):
        """ Power cycles the <node> """
        self.node_name = node_name
        url = self.object_url('node', node_name, 'power_cycle')
        q = requests.post(url, headers={"Authorization": "Basic %s" %self.auth})
        if q.ok:
            return
        elif q.status_code == 409:
            raise BlockedError("Operation blocked by other pending operations")
        elif q.status_code == 500:
            raise NotFoundError("Operation Failed. Contact your system administrator")

    def power_off(self, node_name):
        """ Power offs the <node> """
        self.node_name = node_name
        url = self.object_url('node', node_name, 'power_off')
        q = requests.post(url, headers={"Authorization": "Basic %s" %self.auth})
        if q.ok:
            return
        elif q.status_code == 409:
            raise BlockedError("Operation blocked by other pending operations")
        elif q.status_code == 500:
            raise NotFoundError("Operation Failed. Contact your system administrator")

    def add_nic(self, node_name, nic_name, macaddr):
        """ adds a <nic> from <node>"""
        self.node_name = node_name
        self.nic_name = nic_name
        self.macaddr = macaddr
        url = self.object_url('node', node_name, 'nic', nic_name)
        payload = json.dumps({'macaddr':macaddr})
        q = requests.put(url, headers={"Authorization": "Basic %s" %self.auth}, data=payload)
        if q.ok:
            return
        elif q.status_code == 404:
            raise NotFoundError("Nic cannot be added. Node does not exist.")
        elif q.status_code == 409:
            raise DuplicateError("Nic already exists.")



    def remove_nic(self, node_name, nic_name):
        """ remove a <nic> from <node>"""
        self.node_name = node_name
        self.nic_name = nic_name
        url = self.object_url('node', node_name, 'nic', nic_name)
        q = requests.delete(url, headers={"Authorization": "Basic %s" %self.auth})
        if q.ok:
            return
        elif q.status_code == 404:
            raise NotFoundError("Nic not found. Nothing to delete.")
        elif q.status_code == 409:
            raise BlockedError("Cannot delete nic, diconnect it from network first")


    def connect_network(self, node_name, nic, network, channel):
        """ Connect <node> to <network> on given <nic> and <channel>"""
        pass

    def disconnect_network(self, node_name, nic, network):
        """ Disconnect <node> from <network> on the given <nic>. """
        pass









 
