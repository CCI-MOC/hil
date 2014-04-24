"""Load and query configuration data.

This module handles loading of the haas.cfg file, and querying the options
therein. the `cfg` attribute is an instance of `ConfigParser.RawConfigParser`.
Once `load` has been called, it will be ready to use.
"""

import ConfigParser

cfg = ConfigParser.RawConfigParser()

available_callbacks = []

class BadConfigError(Exception):
    pass

def register_callback(callback_func):
    """ Decorator function to register the validation functions of different
        haas modules.
    """
    global available_callbacks

    available_callbacks.append(callback_func)
    return callback_func

def is_valid_config():
    """ Returns True if the config object is valid, raises BadConfigError
        otherwise.

        Assumptions: The config file has been loaded.
    """
    global cfg

    for cbf in available_callbacks:
        (is_valid, err_msg) = cbf()
        if not(is_valid):
            raise BadConfigError(err_msg)

    return True

def load():
    """Load the configuration from the file 'haas.cfg' in the current directory.

    This must be called once at program startup; no configuration options will
    be available until then.

    If the configuration file is not available, this function will simply load
    an empty configuration (i.e. one with no options).
    """
    global cfg, available_sections

    cfg.read('haas.cfg')
    available_sections = cfg.sections()
    if not(is_valid_config()):
        raise BadConfigError("Please check the config file.")
