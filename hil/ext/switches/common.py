"""Helper methods for switches"""
from hil.config import cfg
from hil import model
from hil.model import db
from hil.errors import BlockedError


def should_save(switch_obj):
    """checks the config file to see if switch should save or not"""
    switch_ext = switch_obj.__class__.__module__
    if cfg.has_option(switch_ext, 'save'):
        if not cfg.getboolean(switch_ext, 'save'):
            return False
    return True


def check_native_networks(nic, op_type, channel):
    """Check to ensure that native network is the first one to be added
    and last one to be removed
    """
    table = model.NetworkAttachment
    query = db.session.query(table).filter(table.nic_id == nic.id)

    if channel != 'vlan/native' and op_type == 'connect' and \
       query.filter(table.channel == 'vlan/native').count() == 0:
        # checks if it is trying to attach a trunked network, and then in
        # in the db see if nic does not have any networks attached natively
        raise BlockedError("Please attach a native network first")
    elif channel == 'vlan/native' and op_type == 'detach' and \
            query.filter(table.channel != 'vlan/native').count() > 0:
        # if it is detaching a network, then check in the database if there
        # are any trunked vlans.
        raise BlockedError("Please remove all trunked Vlans"
                           " before removing the native vlan")
    else:
        return


def parse_vlans(raw_vlans):
    """Method that converts a comma separated list of vlans and vlan ranges to
    a list of individual vlans.

    raw_vlans is a string that can look like:
    '12,14-18,23,28,80-90' or '20' or '20,22' or '20-22'
    """
    range_str = raw_vlans.split(',')

    vlan_list = []
    for num_str in range_str:
        if '-' in num_str:
            num_str = num_str.split('-')
            for x in range(int(num_str[0]), int(num_str[1])+1):
                vlan_list.append(str(x))
        else:
            vlan_list.append(num_str)

    return vlan_list
