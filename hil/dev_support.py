"""Utilities to aid with development."""

import logging
from hil import config
from functools import wraps


def have_dry_run():
    """Detect True if we're executing in dry_run mode, False otherwise."""
    return config.cfg.has_option('devel', 'dry_run')


def no_dry_run(f):
    """A decorator which "disables" a function during a dry run.

    A can specify a `dry_run` option in the `devel` section of `hil.cfg`.
    If the option is present (regardless of its value), any function or
    method decorated with `no_dry_run` will be "disabled." The call will
    be logged (with level `logging.DEBUG`), but will not actually execute.
    The function will instead return 'None'.  Callers of decorated functions
    must accept a None value gracefully.

    The intended use case of `no_dry_run` is to disable functions which
    cannot be run because, for example, the HIL is executing on a
    developer's workstation, which has no configured switch, libvirt, etc.

    If the `dry_run` option is not specified, this decorator has no effect.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        """Wrapper that conditionally disables f, based on config."""
        if have_dry_run():
            logger = logging.getLogger(__name__)
            logger.info('dry run, not executing: %s.%s(*%r,**%r)',
                        f.__module__, f.__name__, args, kwargs)
            return None
        else:
            return f(*args, **kwargs)
    return wrapper
