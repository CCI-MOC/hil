# Copyright 2013-2014 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

"""Load and query configuration data.

This module handles loading of the haas.cfg file, and querying the options
therein. the `cfg` attribute is an instance of `ConfigParser.RawConfigParser`.
Once `load` has been called, it will be ready to use.
"""

import ConfigParser
import logging
from logging import handlers
import importlib
import os
import sys

cfg = ConfigParser.RawConfigParser()
cfg.optionxform = str

def load(filename='haas.cfg'):
    """Load the configuration from the file 'haas.cfg' in the current directory.

    This must be called once at program startup; no configuration options will
    be available until then.

    If the configuration file is not available, this function will simply load
    an empty configuration (i.e. one with no options).
    """
    cfg.read(filename)


def configure_logging():
    """Configure the logger according to the settings in the config file.

    This must be called *after* the config is loaded.
    """
    if cfg.has_option('general', 'log_level'):
        LOG_SET = ["CRITICAL", "DEBUG", "ERROR", "FATAL", "INFO", "WARN",
                   "WARNING"]
        log_level = cfg.get('general', 'log_level').upper()
        if log_level in LOG_SET:
            # Set to mnemonic log level
            logging.basicConfig(level=getattr(logging, log_level))
        else:
            # Set to 'warning', and warn that the config is bad
            logging.basicConfig(level=logging.WARNING)
            logging.getLogger(__name__).warning(
                "Invalid debugging level %s defaulted to WARNING" % log_level)
    else:
        # Default to 'warning'
        logging.basicConfig(level=logging.WARNING)

    # Configure the formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging._defaultFormatter = formatter

    # Add the file handlers for the modules
    if cfg.has_option('general', 'log_dir'):
        log_dir = cfg.get('general', 'log_dir')

        # logging
        log_file = os.path.join(log_dir, 'haas.log')
        logger = logging.getLogger('haas')
        logger.addHandler(logging.handlers.TimedRotatingFileHandler(
            log_file, when='D', interval=1))


def load_extensions():
    """Load extensions.

    Each extension is specified as ``module =`` in the ``[extensions]`` section
    of ``haas.cfg``. This must be called after ``load``.
    """
    if not cfg.has_section('extensions'):
        return
    for name in cfg.options('extensions'):
        importlib.import_module(name)
    for name in cfg.options('extensions'):
        if hasattr(sys.modules[name], 'setup'):
            sys.modules[name].setup()


def setup(filename='haas.cfg'):
    """Do full configuration setup.

    This is equivalent to calling load, configure_logging, and
    load_extensions in sequence.
    """
    load(filename)
    configure_logging()
    load_extensions()
