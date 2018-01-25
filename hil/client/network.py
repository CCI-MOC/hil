"""Client support for network related api calls."""
import json
from hil.client.base import ClientBase


class Network(ClientBase):
        """Consists of calls to query and manipulate network related

        objects and relations.
        """

        def list(self):
            """Lists all networks under HIL """
            url = self.object_url('networks')
            return self.check_response(self.httpClient.request("GET", url))

        def show(self, network):
            """Shows attributes of a network. """
            self.check_reserved('network', network)
            url = self.object_url('network', network)
            return self.check_response(self.httpClient.request("GET", url))

        def create(self, network, owner, access, net_id):
            """Create a link-layer <network>.

            See docs/networks.md for details.
            """
            self.check_reserved('network', network)
            self.check_reserved('owner', owner)
            self.check_reserved('access', access)
            self.check_reserved('Network ID', net_id, slashes_ok=True)
            url = self.object_url('network', network)
            payload = json.dumps({
                'owner': owner, 'access': access,
                'net_id': net_id
                })
            return self.check_response(
                    self.httpClient.request("PUT", url, data=payload)
                    )

        def delete(self, network):
            """Delete a <network>. """
            self.check_reserved('network', network)
            url = self.object_url('network', network)
            return self.check_response(self.httpClient.request("DELETE", url))

        def grant_access(self, project, network):
            """Grants <project> access to <network>. """
            self.check_reserved('project', project)
            self.check_reserved('network', network)
            url = self.object_url(
                    'network', network, 'access', project
                    )
            return self.check_response(self.httpClient.request("PUT", url))

        def revoke_access(self, project, network):
            """Removes access of <network> from <project>. """
            self.check_reserved('project', project)
            self.check_reserved('network', network)
            url = self.object_url(
                    'network', network, 'access', project
                    )
            return self.check_response(self.httpClient.request("DELETE", url))
