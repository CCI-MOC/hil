import json
from haas.client.base import ClientBase
from haas.client import errors


class Network(ClientBase):
        """ Consists of calls to query and manipulate network related
            objects and relations """

        def list(self):
            """ Lists all projects under HIL """
            url = self.object_url('networks')
            return self.check_response(self.s.get(url))

        def show(self, network):
            """ Shows attributes of a network. """
            self.network = network
            url = self.object_url('network', self.network)
            return self.check_response(self.s.get(url))

        def create(self, network, owner, access, net_id):
            """ Create a link-layer <network>. See docs/networks.md for
            details.
            """

            self.network = network
            self.owner = owner
            self.access = access
            self.net_id = net_id

            url = self.object_url('network', self.network)
            payload = json.dumps({
                'owner': self.owner, 'access': self.access,
                'net_id': self.net_id
                })
            return self.check_response(self.s.put(url, data=payload))

        def delete(self, network):
            """ Delete a <network>. """

            self.network = network
            url = self.object_url('network', self.network)
            return self.check_response(self.s.delete(url))

        def grant_access(self, project, network):
            """ Grants <project> access to <network>. """

            self.project = project
            self.network = network

            url = self.object_url(
                    'network', self.network, 'access', self.project
                    )
            return self.check_response(self.s.put(url))

        def revoke_access(self, project, network):
            """ Removes access of <network> from <project>. """

            self.project = project
            self.network = network

            url = self.object_url(
                    'network', self.network, 'access', self.project
                    )
            return self.check_response(self.s.delete(url))
