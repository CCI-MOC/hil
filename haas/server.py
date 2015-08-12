"""Manage server-side startup"""
import sys
# api must be loaded to register the api callbacks, even though we don't
# call it directly from this module:
from haas import model, api
from haas.class_resolver import build_class_map_for
from haas.network_allocator import get_network_allocator


def register_drivers():
    """Put all of the loaded drviers somewhere where the server can find them.

    This must be run *after* extensions have been loaded.
    """
    build_class_map_for(model.Switch)


def validate_state():
    """Do some sanity checking before kicking things off. In particular:

    * Make sure we have a network allocator

    (More checks may be added in the future).

    If any of the checks fail, ``validate_state`` aborts the program.
    """
    if get_network_allocator() is None:
        sys.exit("ERROR: No network allocator registered; make sure your "
                 "haas.cfg loads an extension which provides the network "
                 "allocator.")


def stop_orphan_consoles():
    """Stop any orphaned console logging processes.

    These may exist if HaaS was shut down ucleanly.
    """
    # Stop all orphan console logging processes on startup
    db = model.Session()
    nodes = db.query(model.Node).all()
    for node in nodes:
        node.stop_console()
        node.delete_console()


def api_server_init():
    """Set up the api server's internal state.

    This is a convienience wrapper that calls the other setup routines in
    this module in the correct order, as well as ``model.init_db``
    """
    register_drivers()
    validate_state()
    model.init_db()
    stop_orphan_consoles()
