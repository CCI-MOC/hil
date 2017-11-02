""" This module implements the HIL client library. """

from urlparse import urljoin
import json


class FailedAPICallException(Exception):
    """An exception indicating that the server returned an error."""


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
        """
        Check the response from an API call, and do any needed error handling

        Returns the body of the response as (parsed) JSON, or None if there
        was no body. Raises a FailedAPICallException on any non 2xx status.
        """
        if 200 <= response.status_code < 300:
            try:
                return json.loads(response.content)
            except ValueError:  # No JSON request body; typical
                                # For methods PUT, POST, DELETE
                return
        else:
            e = json.loads(response.content)
            # TODO: I(zenhack) pretty sure only the first case should happen;
            # this was probably an oversight during review. We should check
            # this and fix either the server or the client.
            if e.keys()[0] == 'error':
                raise FailedAPICallException(e['error']['message'])
            else:
                raise FailedAPICallException(e['msg'])
