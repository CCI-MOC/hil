import requests
import keystoneauth1.identity
from keystoneauth1.identity import v3
from keystoneauth1 import session


def db_auth(username, password):
    """ For database as authentication backend, this function prepares
    the default client session.
    """
    s = requests.Session()
    s.auth = (username, password)
    return s


def keystone_auth(
        os_auth_url, os_username, os_password, os_user_domain_id,
        os_project_name, os_project_domain_id
        ):
    """ This functions setup requisites for the  http session when using
    keystone as the aunthentication backend.
    """
    auth = v3.Password(
            auth_url=os_auth_url, username=os_username, password=os_password,
            user_domain_id=os_user_domain_id,
            project_name=os_project_name,
            project_domain_id=os_project_domain_id
            )

    s = session.Session(auth=auth)

    return s
