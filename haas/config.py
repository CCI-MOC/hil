import json

_cfg = None
_validators = []

class ConfigError(Exception):
    pass


def get(name):
    return _cfg[name]


def load(filename=None):
    """Load the configuration from a file.

    By default, the file is 'haas.cfg' in the current directory. This
    can be overridden via the filename argument.

    This function must be called before any of the attributes defined
    here may be used. It is safe to call it more than once.
    """
    global _cfg
    if not filename:
        filename = 'haas.cfg'
    with open(filename) as f:
        _cfg = json.loads(f.read())

    for validate, name in _validators:
        validate(_cfg[name])


def option(name):
    """`option` is a decorator for registering configuration options.

    `name` is the name of the option to register. The decorated function
    will be run after the configuration is loaded, and serves to
    validate the option in question. The function should raise a `ConfigError`
    if the option is invalid.
    """
    def register(validate):
        _validators.append((validate,name))
        if _cfg:
            validate(_cfg[name])
        return validate
    return register
