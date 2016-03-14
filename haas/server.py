"""Manage server-side startup"""
import sys
# api must be loaded to register the api callbacks, even though we don't
# call it directly from this module:
from haas import model, api
from haas.class_resolver import build_class_map_for
from haas.network_allocator import get_network_allocator


def register_drivers():
    """Put all of the loaded drivers somewhere where the server can find them.

    This must be run *after* extensions have been loaded.
    """
    build_class_map_for(model.Switch)
    build_class_map_for(model.Obm)


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

    These may exist if HaaS was shut down uncleanly.
    """
    # Stop all orphan console logging processes on startup
    db = model.Session()
    nodes = db.query(model.Node).all()
    for node in nodes:
        node.obm.stop_console()
        node.obm.delete_console()


def init(init_db=False, stop_consoles=False):
    """Set up the api server's internal state.

    This is a convenience wrapper that calls the other setup routines in
    this module in the correct order, as well as ``model.init_db``
    """
    register_drivers()
    validate_state()
    model.init_db(create=init_db)
    if stop_consoles:
        stop_orphan_consoles()
