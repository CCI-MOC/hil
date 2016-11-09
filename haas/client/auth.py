import requests


def db_auth(username, password):
    """ For database as authentication backend, this function prepares
    the default http client session using requests module.
    """
    s = requests.Session()
    s.auth = (username, password)
    return s

def keystone_auth(parameters):
    """ This functions setup requisites for the  http session when using 
    keystone as the aunthentication backend.
    """
    pass



