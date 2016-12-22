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

    def register(self, switch, subtype, *args):
        """ Registers a switch with name <switch> and
        model <subtype> , and relevant arguments  in <*args>
        """
#       It is assumed that the HIL administrator is aware of 
#       of the switches HIL will control and has read the 
#       HIL documentation to use appropriate flags to register
#       it with HIL.

        pass

    def delete(self, switch):
        self.switch = switch
        url = self.object_url('switch', self.switch)
        q = self.s.delete(url)
        if q.ok:
            return
        elif q.status_code == 404:
            raise errors.NotFoundError(
                    " Operation failed. Resource does not exist."
                    )
        elif q.status_code == 409:
            raise errors.BlockedError(
                    " Operation failed. Cannot delete switch."
                    " Delete its ports first."
                    )

    def show(self, switch):
        """ Shows attributes of <switch>. """

        self.switch = switch
        url = self.object_url('switch', self.switch)
        q = self.s.get(url)
        if q.ok:
            return q.json()
        elif q.status_code == 404:
            raise errors.NotFoundError(
                    "Operation failed. No such switch."
                    )


class Port(ClientBase):
    """ Port related operations. """

    def register(self, switch, port):
        """Register a <port> with <switch>. """
        self.switch = switch
        self.port = port

        url = self.object_url('switch', switch, 'port', port)
        q = self.s.put(url)
        if q.ok:
            return
        elif q.status_code == 409:
            raise errors.DuplicateError( "Port name not unique. ")


    def delete(self, switch, port):
        """ Deletes information of the <port> for <switch> """
        self.switch = switch
        self.port = port

        url = self.object_url('switch', switch, 'port', port)
        q = self.s.delete(url)
        if q.ok:
            return
        elif q.status_code == 404:
            raise errors.NotFoundError( "Port name not found. ")

    def connect_nic(self, switch, port, node, nic):
        """ Connects <port> of <switch> to <nic> of <node>. """
        self.switch = switch
        self.port = port
        self.node = node
        self.nic = nic

        url = self.object_url('switch', switch, 'port', port, 'connect_nic')
        payload = json.dumps({ 'node': self.node, 'nic': self.nic })
        q = self.s.post(url, payload)
        if q.ok:
            return
        elif q.status_code == 409:
            raise errors.DuplicateError( "Port or Nic already connected. ")


    def detach_nic(self, switch, port):
        """" Detaches <port> of <switch>. """
        self.switch = switch
        self.port = port
        url = self.object_url('switch', switch, 'port', port, 'detach_nic')
        q = self.s.post(url)
        if q.ok:
            return
        elif q.status_code == 404:
            raise errors.NotFoundError(
                    "Operation Failed. The relationship does not exist. "
                    )


