"""Collection of some common utility functions.
"""

import socket

def _is_valid_ipv4(ip):
    """Returns True if the ip address string is a valid IPv4 address,
       False otherwise.
    
       This function is internal to this module.
    """
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        return False

def _is_valid_ipv6(ip):
    """Returns True if the ip address string is a valid IPv6 address,
       False otherwise.
    
       This function is internal to this module.
    """
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except socket.error:
        return False

def is_valid_ip(ip):
    """Returns True if the ip address string is a valid IP address,
       False otherwise.
    """
    return (_is_valid_ipv4(ip) or _is_valid_ipv6(ip))
