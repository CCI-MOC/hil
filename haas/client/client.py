from haas.client.node import Node
from haas.client.project import Project
from haas.client.switch import Switch
from haas.client.switch import Port
from haas.client.network import Network
from haas.client.user import User
import abc
import requests


class HTTPClient(object):
    """An HTTP client.

    Makes HTTP requests on behalf of the HaaS CLI. Responsible for adding
    authentication information to the request.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def request(method, url, data=None, params=None):
        """Make an HTTP request

        Makes an HTTP request on URL `url` with method `method`, request body
        `data`(if supplied) and query parameter `params`(if supplied). May add
        authentication or other backend-specific information to the request.

        Parameters
        ----------

        method : str
            The HTTP method to use, e.g. 'GET', 'PUT', 'POST'...
        url : str
            The URL to act on
        data : str, optional
            The body of the request
        params : dictionary, optional
            The query parameter, e.g. {'key1': 'val1', 'key2': 'val2'},
            dictionary key can't be `None`

        Returns
        -------

        requests.Response
            The HTTP response
        """


class RequestsHTTPClient(requests.Session, HTTPClient):
    """An HTTPClient which uses the requests library.

    Note that this doesn't do anything over `requests.Session`; that
    class already implements the required interface. We declare it only
    for clarity.
    """


class KeystoneHTTPClient(HTTPClient):
    """An HTTPClient which authenticates with Keystone.

    This uses an instance of python-keystoneclient's Session class
    to do its work.
    """

    def __init__(self, session):
        """Create a KeystoneHTTPClient

        Parameters
        ----------

        session : keystoneauth1.Session
            A keystone session to make the requests with
        """
        self.session = session

    def request(self, method, url, data=None, params=None):
        """Make an HTTP request using keystone for authentication.

        Smooths over the differences between python-keystoneclient's
        request method that specified by HTTPClient
        """
        # We have to import this here, since we can't assume the library
        # is available from global scope.
        from keystoneauth1.exceptions.http import HttpError

        try:
            # The order of these parameters is different that what
            # we expect, but the names are the same:
            return self.session.request(method=method,
                                        url=url,
                                        data=data,
                                        params=params)
        except HttpError as e:
            return e.response


class Client(object):

    def __init__(self, endpoint, httpClient):
        self.httpClient = httpClient
        self.endpoint = endpoint
        self.node = Node(self.endpoint, self.httpClient)
        self.project = Project(self.endpoint, self.httpClient)
        self.switch = Switch(self.endpoint, self.httpClient)
        self.port = Port(self.endpoint, self.httpClient)
        self.network = Network(self.endpoint, self.httpClient)
        self.user = User(self.endpoint, self.httpClient)
