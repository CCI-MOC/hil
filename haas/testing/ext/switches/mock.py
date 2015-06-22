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

Useful for testing switch drivers such as the simple and complex VLAN drivers.
This driver will probably not work correctly outside of the testing
environment.

If there are two switches in the config that have the same name, their changes
will clash with each other.
"""

from haas.model import Switch
from schema import Schema
from sqlalchemy import Column, Integer, ForeignKey

LOCAL_STATE = {}


class MockSwitch(Switch):
    id = Column(Integer, ForeignKey('switch.id'), primary_key=True)

    api_name = 'http://schema.massopencloud.org/haas/switches/mock'

    __mapper_args__ = {
        'polymorphic_identity': api_name,
    }

    @staticmethod
    def validate(kwargs):
        Schema({}).validate(kwargs)

    def apply_networking(self, net_map):

        global LOCAL_STATE

        if self.label not in LOCAL_STATE:
            LOCAL_STATE[self.label] = {}

        for port in net_map:
            LOCAL_STATE[self.label][port] = net_map[port]
