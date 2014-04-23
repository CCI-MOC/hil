"""Load and query configuration data.

This module handles loading of the haas.cfg file, and querying the options
therein. the `cfg` attribute is an instance of `ConfigParser.RawConfigParser`.
Once `load` has been called, it will be ready to use.
"""

import ConfigParser

cfg = ConfigParser.RawConfigParser()

mandatory_sections = ["general", "headnode"]
available_sections = []

class BadConfigError(Exception):
    pass

def is_valid_config(cfg):
    """ Returns true if the config object is valid, false (w/ the error string)
        otherwise

        Assumptions: The global variable: available_sections has already been
                     populated from the config file
    """
    global mandatory_sections, available_sections

    for section in mandatory_sections:
        if not(section in available_sections):
           return (False, "Missing mandatory \"" + section + "\" section")
    return (True, None)

def get_value_from_config(section_name, option_name):
    """ Returns value of an attribute from the config object, or None if the
        attribute is not present
    """
    value = None
    try:
        value = cfg.get(section_name, option_name)
    except (NoSectionError, NoOptionError):
        return None
    return value

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
    (is_valid, err_msg) = is_valid_config(cfg)
    if not is_valid:
        raise BadConfigError("Please check the config file. Error: " + err_msg)
