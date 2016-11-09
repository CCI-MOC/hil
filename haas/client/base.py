""" This module implements the HaaS client library. """

import requests
import os
import json
from haas.client import errors
from urlparse import urljoin


class ClientBase(object):
    """ Main class which contains all the methods to
    -- ensure input complies to API requisites
    -- generates correct format for server API on behalf of the client
    -- parses output from received from the server.
    In case of errors recieved from server, it will generate appropriate
    appropriate message.
    """

    def __init__(self, endpoint=None, sess=None):
        """ Initialize an instance of the library with following parameters.
        endpoint: stands for the http endpoint eg. endpoint=http://127.0.0.1
        user: username as which you wish to connect to HaaS
        password: password for the 'user' as decribed above.
        Currently all this information is fetched from the user's environment.
        """
        self.endpoint = endpoint
        self.s = sess

        if None in [self.endpoint, self.s]:
            raise LookupError(
                    "Insufficient attributes to establish "
                    "connection with HaaS server")

    def object_url(self, *args):
        """Generate URL from combining endpoint and args as relative URL"""
        rel = "/".join(args)
        url = urljoin(self.endpoint, rel)
        return url
