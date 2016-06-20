from haas.client.base import *
from haas.client.client_errors import *


class Node(ClientBase):
    """ Consists of calls to query and manipulate node related
    objects and relations """

    def free_list(self):
        """ List all nodes that HIL manages """
        url = self.object_url('/free_nodes')
        q = requests.get(url, headers={"Authorization": "Basic %s" % self.auth})
        if q.ok:
            return q.json()
        elif q.status_code == 401:
            raise AuthenticationError("Make sure credentials match chosen authentication backend.")






