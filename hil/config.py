"""Load and query configuration data.

This module handles loading of the hil.cfg file, and querying the options
therein. the `cfg` attribute is an instance of `ConfigParser.RawConfigParser`.
Once `load` has been called, it will be ready to use.
"""

import ConfigParser
import logging.handlers
import importlib
from schema import Schema, Optional, Use, And, Or
import os
import sys
from urlparse import urlparse
import errno

cfg = ConfigParser.RawConfigParser()
cfg.optionxform = str


def string_is_bool(option):
    """Check if a string matches ConfigParser's definition of a bool"""
    return And(Use(str.lower), Or('true', 'yes', 'on', '1',
                                  'false', 'no', 'off', '0')).validate(option)


def string_is_web_url(option):
    """Check if a string is a valid web URL"""
    return And(lambda s: urlparse(s).scheme != '',
               lambda s: urlparse(s).netloc != '').validate(option)


def string_is_db_uri(option):
    """Check if a string is a valid DB URI"""
    return And(Use(lambda s: urlparse(s).scheme),
               Or('postgresql', 'sqlite')).validate(option)


def string_is_dir(option):
    """Check if a string is a valid directory path"""
    return Use(os.path.isabs).validate(option)


def string_is_log_level(option):
    """Check if a string is a valid log level"""
    return And(Use(str.lower), Or('debug', 'info', 'warn', 'warning', 'error',
                                  'critical', 'fatal')).validate(option)


def string_has_vlans(option):
    """Check if a string is a valid list of VLANs"""
    for r in option.split(","):
        r = r.strip().split("-")
        if not all(s.isdigit() and 0 < int(s) <= 4096 for s in r):
            return False
    return True


# Note: headnode section receiving minimal checking due to soon replacement
core_schema = {
    Optional('general'): {
        'log_level': string_is_log_level,
        Optional('log_dir'): string_is_dir,
    },
    Optional('auth'): {
        Optional('require_authentication'): string_is_bool,
    },
    'headnode': {
        'trunk_nic': str,
        'base_imgs': str,
        'libvirt_endpoint': str,
    },
    'client': {
        Optional('endpoint'): string_is_web_url,
    },
    'database': {
        'uri': string_is_db_uri,
    },
    Optional('devel'): {
        Optional('dry_run'): string_is_bool,
    },
    Optional('maintenance'): {
        Optional('maintenance_project'): str,
        Optional('url'): string_is_web_url,
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
        # Catch bad log directories
        try:
            logger.addHandler(logging.handlers.TimedRotatingFileHandler(
                log_file, when='D', interval=1))
        except IOError as e:
            if e.errno == errno.ENOENT:
                sys.exit("Error: log directory does not exist")
            elif e.errno == errno.EACCES:
                sys.exit("Error: insufficient permissions to "
                         "access log directory")
            else:
                raise(e)


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
    load_extensions()
    validate_config()
    configure_logging()
