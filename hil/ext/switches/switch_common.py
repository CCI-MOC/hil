"""Helper methods common to all switches"""
from hil.config import cfg


def _should_save(switch_type):
    """checks the config file to see if switch should save or not"""

    switch_ext = 'hil.ext.switches.' + switch_type
    if cfg.has_option(switch_ext, 'save'):
        if not cfg.getboolean(switch_ext, 'save'):
            return False
    return True
