# Copyright 2015-2016 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language
# governing permissions and limitations under the License.

"""MockObm driver for implementing out of band management. """

from sqlalchemy import Column, String, ForeignKey
import schema

from hil.model import Obm
from hil.dev_support import no_dry_run

from os.path import join, dirname
from hil.migrations import paths
from hil.model import BigIntegerType

paths[__name__] = join(dirname(__file__), 'migrations', 'mock')


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

    @no_dry_run
    def power_cycle(self, force):
        return

    @no_dry_run
    def power_off(self):
        return

    def require_legal_bootdev(self, dev):
        return

    def set_bootdev(self, dev):
        return

    @no_dry_run
    def start_console(self):
        return

    @no_dry_run
    def stop_console(self):
        return

    @no_dry_run
    def delete_console(self):
        return

    @no_dry_run
    def get_console(self):
        return

    @no_dry_run
    def get_console_log_filename(self):
        return
