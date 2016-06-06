""" This module implements the HaaS client library. """

import requests
import os
import json
from urlparse import urljoin
from requests.exceptions import ConnectionError

from client_errors import *


class hilClientLib:
    """ Main class which contains all the methods to
    -- ensure input complies to API requisites
    -- generates correct format for server API on behalf of the client
    -- parses output from received from the server.
    In case of errors recieved from server, it will generate appropriate
    appropriate message.
    """


    def __init__(self, endpoint=None, user=None, password=None):
        """ Initialize an instance of the library with following parameters.
        endpoint: stands for the http endpoint eg. endpoint=http://127.0.0.1
        user: username as which you wish to connect to HaaS
        password: password for the 'user' as decribed above.
        Currently all this information is fetched from the user's environment.
        """
        self.endpoint = endpoint or os.environ.get('HAAS_ENDPOINT')
        self.user = user or os.environ.get('HAAS_USERNAME')
        self.password = password or os.environ.get('HAAS_PASSWORD')

        if None in [self.endpoint, self.user, self.password]:
            raise LookupError("Insufficient attributes to establish connection with HaaS server")

    def object_url(self, *args):
        """Generate URL from combining endpoint and args as relative URL"""
        rel = "/".join(args)
        url = urljoin(self.endpoint, rel)
        return url


## ** QUERY COMMANDS **
    def list_free_nodes(self):
        """ Reports available nodes in the free_pool."""

        url = self.object_url('/free_nodes')
        try:
            query = requests.get(url)
        except ConnectionError as err:
            print ("ERROR: Either HIL server is not running or some network issue is stopping me from reaching the server ", err) 
        else:
            return query.json



    def user_create(self, username, password, role):
        """Create a user <username> with password <password>.
        It must be assigned a role either 'admin' or 'regular'
        """
        #POINT TO DISCUSS: 
        #Should role default to 'regular' so that users will
        #use the extra flag only in case of making other 'admin' users.

        url = object_url('/auth/basic/user', username)
        if role not in ('admin', 'regular'):
            raise TypeError("role must be either 'admin' or 'regular'")

        ## This is incomplete. Interfacing with corresponding API call needs some thinking.

    def node_register(node, subtype, *args):
        """Register a node named <node>, with the given type
        eg. If obm if of type: ipmi then provide arguments relevant to the driver
        "ipmi", <hostname>, <ipmi-username>, <ipmi-password>
        """
        #FIXME: This needs to have a corresponding API provided by the drivers themselves
        #Also, there has to be a way to expose activated drivers to Users.
        #Library should be able to provide correct handles generic hooks for all of the drivers.
        #My General feeling is that api library should know minimal about the server.
        #Currently it violates the Model-View-Controller paradigm, since it has to know 
        #Which drivers are available and active on the server and what does the third party driver
        #api name looks like. Library should not know all this.

        obm_api = "http://schema.massopencloud.org/haas/v0/obm/"







