"""Load and query configuration data.

This module handles loading of the haas.cfg file, and querying the options
therein. the `cfg` attribute is an instance of `ConfigParser.RawConfigParser`.
Once `load` has been called, it will be ready to use.
"""

import ConfigParser

cfg = ConfigParser.RawConfigParser()

def load():
    """Load the configuration from the file 'haas.cfg' in the current directory.

    This must be called once at program startup; no configuration options will
    be available until then.

    If the configuration file is not available, this function will simply load
    an empty configuration (i.e. one with no options).
    """
    cfg.read('haas.cfg')
