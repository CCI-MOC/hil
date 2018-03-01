"""Load and query configuration data.

This module handles loading of the hil.cfg file, and querying the options
therein. the `cfg` attribute is an instance of `ConfigParser.RawConfigParser`.
Once `load` has been called, it will be ready to use.
"""

import ConfigParser
import logging.handlers
import importlib
from schema import Schema, Optional
import os
import sys

cfg = ConfigParser.RawConfigParser()
cfg.optionxform = str

core_schema = {
    Optional('general'): {
        'log_level': str,
        Optional('log_dir'): str,
    },
    Optional('auth'): {
        Optional('require_authentication'):
            lambda s: string_is_bool(s),
    },
    'headnode': {
        'trunk_nic': str,
        'base_imgs': str,
        'libvirt_endpoint': str,
    },
    'client': {
        Optional('endpoint'): str,
    },
    'database': {
        'uri': str,
    },
    Optional('devel'): {
        Optional('dry_run'):
            lambda s: string_is_bool(s),
    },
    Optional('maintenance'): {
        Optional('maintenance_project'): str,
        Optional('url'): str,
        Optional('shutdown'): '',
    },
    Optional('network-daemon'): {
        Optional('sleep_time'): int,
    },
    'extensions': {
        Optional(str): '',
    },
}


def load(filename='hil.cfg'):
    """Load the configuration from the file 'hil.cfg' in the current directory.

    This must be called once at program startup; no configuration options will
    be available until then.

    If the config file is not found, it will simply exit.
    """
    opened_file = cfg.read(filename)
    if filename not in opened_file:
        sys.exit("Config file not found. Please create hil.cfg")


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
            logging.getLogger(__name__).warn(
                "Invalid debugging level %s defaulted to WARNING", log_level)
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
        log_file = os.path.join(log_dir, 'hil.log')
        logger = logging.getLogger('hil')
        logger.addHandler(logging.handlers.TimedRotatingFileHandler(
            log_file, when='D', interval=1))


def load_extensions():
    """Load extensions.

    Each extension is specified as ``module =`` in the ``[extensions]`` section
    of ``hil.cfg``. This must be called after ``load``.
    """
    if not cfg.has_section('extensions'):
        return
    for name in cfg.options('extensions'):
        importlib.import_module(name)
    for name in cfg.options('extensions'):
        if hasattr(sys.modules[name], 'setup'):
            sys.modules[name].setup()


def validate_config():
    """Validate the current config file"""
    cfg_dict = dict()
    for section in cfg.sections():
        cfg_dict[section] = dict(cfg.items(section))
    validated = Schema(core_schema).validate(cfg_dict)
    assert validated == cfg_dict


def setup(filename='hil.cfg'):
    """Do full configuration setup.

    This is equivalent to calling load, configure_logging, and
    load_extensions in sequence.
    """
    load(filename)
    configure_logging()
    load_extensions()
    validate_config()


def string_is_bool(option):
    """Check if a string matches ConfigParser's definition of a bool"""
    return option.lower() in ['true', 'yes', 'on', '1',
                              'false', 'no', 'off', '0']
