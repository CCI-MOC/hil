import json
from haas.client.base import ClientBase
from haas.client import errors


class Network(ClientBase):
        """ Consists of calls to query and manipulate project related
            objects and relations """

        def list(self):
            """ Lists all projects under HIL """
            url = self.object_url('/networks')
            q = self.s.get(url)
            if q.ok:
                return q.json()
            elif q.status_code == 401:
                raise errors.AuthenticationError(
                        "Make sure credentials match "
                        "chosen authentication backend."
                        )
