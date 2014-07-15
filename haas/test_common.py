from functools import wraps
from haas.model import *
from haas.config import cfg

def newDB():
    """Configures and returns an in-memory DB connection"""
    init_db(create=True,uri="sqlite:///:memory:")
    return Session()

def releaseDB(db):
    """Do we need to do anything here to release resources?"""
    pass


def clear_configuration(f):
    """A decorator which clears all HaaS configuration both before and after
    calling the function.  Used for tests which require a specific
    configuration setup.
    """

    def config_clear():
        for section in cfg.sections():
            cfg.remove_section(section)

    @wraps(f)
    def wrapped(self):
        config_clear()
        f(self)
        config_clear()

    return wrapped


def database_only(f):
    """A decorator which runs the given function on a fresh memory-backed
    database, and a config that is empty except for making the 'null' backend
    active.  Used for testing functions that pertain to the database but not
    the backend.
    """

    def config_initialize():
        # Use the 'null' backend for these tests
        cfg.add_section('general')
        cfg.set('general', 'active_switch', 'null')

    @wraps(f)
    @clear_configuration
    def wrapped(self):
        config_initialize()
        db = newDB()
        f(self, db)
        releaseDB(db)

    return wrapped
