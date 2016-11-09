import json
from haas.client.base import ClientBase
from haas.client import errors


class Switch(ClientBase):
    """ Consists of calls to query and manipulate node related
    objects and relations """

    def list(self):
        """ List all nodes that HIL manages """
        url = self.object_url('/switches')
        q = self.s.get(url)
        if q.ok:
            return q.json()
        elif q.status_code == 401:
            raise errors.AuthenticationError(
                    "Make sure credentials match "
                    "chosen authentication backend."
                    )
