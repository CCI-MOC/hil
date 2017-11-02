"""Helper methods common to all switches"""
from hil.config import cfg


def should_save(switch_obj):
    """checks the config file to see if switch should save or not"""
    switch_ext = switch_obj.__class__.__module__
    if cfg.has_option(switch_ext, 'save'):
        if not cfg.getboolean(switch_ext, 'save'):
            return False
    return True
