# Copyright 2013-2014 Massachusetts Open Cloud Contributors
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

"""This module contains a set of tools that are used by specific switch
drivers.  Functions contained within this module are generic, and are
not specific to any one switch."""

from haas import network_allocator


def get_new_network_id(db):
    return network_allocator._network_allocator.get_new_network_id(db)


def free_network_id(db, net_id):
    return network_allocator._network_allocator.free_network_id(db, net_id)


def init_db(create=False):
    if create:
        network_allocator._network_allocator.populate()
