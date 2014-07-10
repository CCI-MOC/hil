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


def clear_config_decorator(f):
    def config_clear():
        for section in cfg.sections():
            cfg.remove_section(section)

    @wraps(f)
    def wrapped(self):
        config_clear()
        f(self)
        config_clear()

    return wrapped


def null_config_decorator(f):
    def config_initialize():
        # Use the 'null' backend for these tests
        cfg.add_section('general')
        cfg.set('general', 'active_switch', 'null')

    @wraps(f)
    @clear_config_decorator
    def wrapped(self):
        config_initialize()
        db = newDB()
        f(self, db)
        releaseDB(db)

    return wrapped
