"""Network switch drivers for the HaaS.

This package provides HaaS drivers for various network switches. The
functions in the top-level module are no-ops, but serve to document the
interface shared by all of the drivers.
"""

def set_access_vlan(port_id, vlan_id):
    """Sets switch port #`port_id` to access mode, using vlan #`vlan_id`.

    TODO: need to define how error handling works for this function.
    """

