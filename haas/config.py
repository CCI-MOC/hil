import json

_cfg = None
trunk_nic = None
file_names = None

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

    global trunk_nic, file_names
    trunk_nic = _cfg["trunk_nic"]
    file_names = _cfg["file_names"]
