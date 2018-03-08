"""This module sets up a HIL client"""

import sys
import os
import requests

from hil.client.client import Client, RequestsHTTPClient

def setup_http_client():
    """Set `http_client` to a valid instance of `HTTPClient`

    and pass it as parameter to initialize the client library.

    Sets http_client to an object which makes HTTP requests with
    authentication. It chooses an authentication backend as follows:

    1. If the environment variables HIL_USERNAME and HIL_PASSWORD
       are defined, it will use HTTP basic auth, with the corresponding
       user name and password.
    2. If the `python-keystoneclient` library is installed, and the
       environment variables:

           * OS_AUTH_URL
           * OS_USERNAME
           * OS_PASSWORD
           * OS_PROJECT_NAME

       are defined, Keystone is used.
    3. Otherwise, do not supply authentication information.

    This may be extended with other backends in the future.

    `http_client` is also passed as a parameter to the client library.
    Until all calls are moved to client library, this will support
    both ways of intereacting with HIL.
    """
    # First try basic auth:
    ep = (
            os.environ.get('HIL_ENDPOINT') or
            sys.stdout.write("Error: HIL_ENDPOINT not set \n")
            )
    basic_username = os.getenv('HIL_USERNAME')
    basic_password = os.getenv('HIL_PASSWORD')
    if basic_username is not None and basic_password is not None:
        # For calls with no client library support yet.
        # Includes all headnode calls; registration of nodes and switches.
        http_client = RequestsHTTPClient()
        http_client.auth = (basic_username, basic_password)
        # For calls using the client library
        return Client(ep, http_client)
    # Next try keystone:
    try:
        from keystoneauth1.identity import v3
        from keystoneauth1 import session
        os_auth_url = os.getenv('OS_AUTH_URL')
        os_password = os.getenv('OS_PASSWORD')
        os_username = os.getenv('OS_USERNAME')
        os_user_domain_id = os.getenv('OS_USER_DOMAIN_ID') or 'default'
        os_project_name = os.getenv('OS_PROJECT_NAME')
        os_project_domain_id = os.getenv('OS_PROJECT_DOMAIN_ID') or 'default'
        if None in (os_auth_url, os_username, os_password, os_project_name):
            raise KeyError("Required openstack environment variable not set.")
        auth = v3.Password(auth_url=os_auth_url,
                           username=os_username,
                           password=os_password,
                           project_name=os_project_name,
                           user_domain_id=os_user_domain_id,
                           project_domain_id=os_project_domain_id)
        sess = session.Session(auth=auth)
        http_client = KeystoneHTTPClient(sess)
        return Client(ep, http_client)
    except (ImportError, KeyError):
        pass
    # Finally, fall back to no authentication:
    http_client = requests.Session()
    return Client(ep, http_client)