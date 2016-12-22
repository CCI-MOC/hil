import json
from haas.client.base import ClientBase
from haas.client import errors


class Network(ClientBase):
        """ Consists of calls to query and manipulate network related
            objects and relations """

        def list(self):
            """ Lists all projects under HIL """
            url = self.object_url('networks')
            q = self.s.get(url)
            if q.ok:
                return q.json()
            elif q.status_code == 401:
                raise errors.AuthenticationError(
                        "Make sure credentials match "
                        "chosen authentication backend."
                        )
        def show(self, network):
            """ Shows attributes of a network. """
            self.network = network
            url = self.object_url('network', self.network)
            q = self.s.get(url)
            if q.ok:
                return q.json()
            elif q.status_code == 401:
                raise errors.AuthenticationError(
                        "Make sure credential match."
                        "chosen authentication backend."
                        )
            elif q.status_code == 404:
                raise errors.NotFoundError(
                        "Network does not exist."
                        )


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
                'owner': self.owner, 'access': self.access, 'net_id': self.net_id
                })
            q = self.s.put(url, data=payload)
            if q.ok:
                return
            elif q.status_code == 409:
                raise errors.DuplicateError(
                        "Network name already exists. "
                        )
            elif q.status_code == 404:
                raise errors.NotFoundError(
                        "Operation failed. Missing Parameters. "
                        )

        def delete(self, network):
            """ Delete a <network>. """

            self.network = network
            url = self.object_url('network', self.network)
            q = self.s.delete(url)
            if q.ok:
                return
            elif q.status_code == 404:
                raise errors.NotFoundError(
                        "Operation failed. No such network. "
                        )

        def grant_access(self, project, network):
            """ Grants <project> access to <network>. """

            self.project = project
            self.network = network

            url = self.object_url(
                    'network', self.network, 'access', self.project
                    )
            q = self.s.put(url)
            if q.ok:
                return
            elif q.status_code == 404:
                raise errors.NotFoundError(
                        "Operation failed. Resource does not exist. "
                        )
            elif q.status_code == 409:
                raise errors.DuplicateError(
                        "Access relationship already exists. "
                        )


        def revoke_access(self, project, network):
            """ Removes access of <network> from <project>. """


            self.project = project
            self.network = network

            url = self.object_url(
                    'network', self.network, 'access', self.project
                    )
            q = self.s.delete(url)
            if q.ok:
                return
            elif q.status_code == 404:
                raise errors.NotFoundError(
                        "Operation failed. Resource or relationship "
                        "does not exist. "
                        )


