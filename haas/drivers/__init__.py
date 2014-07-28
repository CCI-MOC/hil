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

"""Network switch drivers for the HaaS.

This package provides HaaS drivers for various network switches. The
functions in the top-level module should not be used; they only exist
as a place to document the interface shared by all of the drivers.

Port IDs and network IDs should both be strings.  The content of them will be
driver-specific.

Note that get_new_network_id and free_network_id both accept a database
connection.  They should not commit any changes---this way, if there is a
crash between the function returning, and the network actually being assigned
or removed from a network object, the entire transaction is cancelled.

Stateless drivers such as 'null' don't need to worry about this.  Drivers
whose state is in the database, such as 'dell', require this.  Drivers with
external state may need to do some difficult work to make this work.

"""


def apply_networking(net_map):
    """Takes in a dictionary, mapping port IDs to network IDs.

    For each key-value pair (port, network) in the dictionary, set that port
    to access that network.  If network is None, set it to access nothing.
    """

def get_new_network_id(db):
    """Gets a new network ID, valid for this driver.  Returns 'None' if there
    are no more possible IDs available.  Pass in the database connection, to
    make the allocation part of the current transaction.
    """

def free_network_id(db, net_id):
    """Marks a network ID as unused, so that it can be re-used for a new
    network.  Can be a no-op on some drivers.  Pass in the database
    connection, to make the freeing part of the current transaction.
    """

def init_db(create=False):
    """Called upon startup with 'create=False', and upon 'haas init_db' with
    'create=True'.

    If 'create==True', the driver should initialize any database tables and/or
    objects that it needs to have in order to function correctly.

    If 'create==False', the driver should perform any actions that must happen
    on server startup.
    """
    # XXX This is gross.  Right now there are three different things called
    # 'init_db': a function in model.py, the driver function, and the API
    # call.  They all do different things.
