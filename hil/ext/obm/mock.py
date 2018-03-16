"""MockObm driver for implementing out of band management. """

from sqlalchemy import Column, String, ForeignKey
import schema

from hil.model import Obm

from os.path import join, dirname
from hil.migrations import paths
from hil.model import BigIntegerType
from collections import defaultdict

paths[__name__] = join(dirname(__file__), 'migrations', 'mock')

LOCAL_STATE = defaultdict(lambda: defaultdict(dict))


class MockObm(Obm):
    """Mock OBM object, for use in tests."""

    id = Column(BigIntegerType, ForeignKey('obm.id'), primary_key=True)
    host = Column(String, nullable=False)
    user = Column(String, nullable=False)
    password = Column(String, nullable=False)

    api_name = 'http://schema.massopencloud.org/haas/v0/obm/mock'

    __mapper_args__ = {
        'polymorphic_identity': api_name,
        }

    @staticmethod
    def validate(kwargs):
        schema.Schema({
            'type': MockObm.api_name,
            'host': basestring,
            'user': basestring,
            'password': basestring,
            }).validate(kwargs)

    def power_cycle(self, force):
        return

    def power_off(self):
        return

    def require_legal_bootdev(self, dev):
        return

    def set_bootdev(self, dev):
        return

    def start_console(self):
        state = LOCAL_STATE[self.id]
        state['console'] = True
        return

    def stop_console(self):
        state = LOCAL_STATE[self.id]
        state['console'] = False
        return

    def delete_console(self):
        return

    def get_console(self):
        state = LOCAL_STATE[self.id]
        if state['console']:
            return "Some console output"

    def get_console_log_filename(self):
        return
