""" This module implements the HIL client library. """

from urlparse import urljoin


class FailedAPICallException(Exception):
    pass


class ClientBase(object):
    """Main class which contains all the methods to

    -- ensure input complies to API requisites
    -- generates correct format for server API on behalf of the client
    -- parses output from received from the server.
    In case of errors recieved from server, it will generate appropriate
    appropriate message.
    """

    def __init__(self, endpoint, httpClient):
        """ Initialize an instance of the library with following parameters.

       endpoint: stands for the http endpoint eg. endpoint=http://127.0.0.1
       sess: depending on the authentication backend (db vs keystone) the
       parameters required to make up the session vary.
       user: username as which you wish to connect to HIL
       Currently all this information is fetched from the user's environment.
        """
        self.endpoint = endpoint
        self.httpClient = httpClient

    def object_url(self, *args):
        """Generate URL from combining endpoint and args as relative URL"""
        rel = "/".join(args)
        url = urljoin(self.endpoint, rel)
        return url

    def check_response(self, response):
        if response.ok:
            if response.request.method == 'GET':
                return response.json()
            else:  # For methods PUT, POST, DELETE
                return
        else:
            e = response.json()
            raise FailedAPICallException(e['msg'])
