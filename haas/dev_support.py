import logging
from haas import config


def no_dry_run(f):
    """A decorator which "disables" a function during a dry run.

    A can specify a `dry_run` option in the `devel` section of `haas.cfg`.
    If the option is present (regardless of its value), any function or
    method decorated with `no_dry_run` will be "disabled." The call will
    be logged (with level `logging.DEBUG`), but will not actually execute.
    callers of decorated functions should not rely on the return value of
    those functions; the return value during a dry run is unspecified.

    The intended use case of `no_dry_run` is to disable functions which
    cannot be run because, for example, the HaaS is executing on a
    developer's workstation, which has no configured switch, libvirt, etc.

    If the `dry_run` option is not specified, this decorator has no effect.
    """
    def wrapper(*args, **kwargs):
        if config.cfg.has_option('devel', 'dry_run'):
            logger = logging.getLogger(__name__)
            logger.debug('dry run, not executing: %s.%s(*%r,**%r)' %
                         (f.__module__, f.__name__, args, kwargs))
        else:
            f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # This will make debugging a bit nicer.
    return wrapper
