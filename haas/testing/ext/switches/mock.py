# Copyright 2013-2015 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

"""A switch driver that maintains local state only.

Meant for use in the test suite.
"""

from haas.model import Switch
from schema import Schema
from sqlalchemy import Column, Integer, ForeignKey

LOCAL_STATE = {}


class MockSwitch(Switch):
    """A switch which stores configuration in memory.

    This class conforms to the interface specified by ``haas.model.Switch``.
    It's implementation is connectionless, so it is it's own session object as
    suggested int the superclass's documentation.
    """
    id = Column(Integer, ForeignKey('switch.id'), primary_key=True)

    api_name = 'http://schema.massopencloud.org/haas/switches/mock'

    __mapper_args__ = {
        'polymorphic_identity': api_name,
    }

    @staticmethod
    def validate(kwargs):
        Schema({}).validate(kwargs)

    def session(self):
        return self

    def apply_networking(self, net_map):

        global LOCAL_STATE

        if self.label not in LOCAL_STATE:
            LOCAL_STATE[self.label] = {}

        for port in net_map:
            channel = net_map[port]['channel']
            network = net_map[port]['network']
            if channel is None:
                del LOCAL_STATE[self.label][port][network]
            else:
                LOCAL_STATE[self.label][port][network] = channel

    def disconnect(self):
        pass
