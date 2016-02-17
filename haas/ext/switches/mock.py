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

from collections import defaultdict
from haas.model import Switch
import schema
#from schema import Schema
from sqlalchemy import Column, Integer, ForeignKey, String

LOCAL_STATE = defaultdict(lambda: defaultdict(dict))


class MockSwitch(Switch):
    """A switch which stores configuration in memory.

    This class conforms to the interface specified by ``haas.model.Switch``.
    It's implementation is connectionless, so it is it's own session object as
    suggested int the superclass's documentation.
    """

    api_name = 'http://schema.massopencloud.org/haas/v0/switches/mock'

    __mapper_args__ = {
        'polymorphic_identity': api_name,
    }
    
    id = Column(Integer, ForeignKey('switch.id'), primary_key=True)
    hostname = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)

    @staticmethod
    def validate(kwargs):
        schema.Schema({
            'username': basestring,
            'hostname': basestring,
            'password': basestring,
        }).validate(kwargs)


#    @staticmethod
#    def validate(kwargs):
#        Schema({}).validate(kwargs)

    def session(self):
        return self

    def apply_networking(self, action):
        state = LOCAL_STATE[self.label]
        port = action.nic.port.label

        if action.new_network is None:
            del state[port][action.channel]
        else:
            state[port][action.channel] = action.new_network.network_id

    def disconnect(self):
        pass

    def get_port_networks(self, ports):
        state = LOCAL_STATE[self.label]
        ret = {}
        for port in ports:
            ret[port] = []
            for chan, net in state[port.label].iteritems():
                if net is not None:
                    ret[port].append((chan, net))
        return ret
