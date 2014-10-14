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

"""Performs deferred networking actions."""

from haas import model, config
import logging, importlib

def apply_networking():
    """Do each networking action in the journal, then cross them off.

    Returns False if the journal was empty, and True if it wasn't.  This way,
    the caller knows whether anything was done.  If something was done, then
    the caller can run this function again immediately.  If nothing was done,
    then the caller should not do that.
    """
    db = model.Session()

    # Get the journal enries
    network_map = {}
    actions = db.query(model.NetworkingAction).all()

    if actions == []:
        # No actions to perform.  Return False immediately.
        db.commit()
        return False

    for action in actions:
        nic = action.nic
        network = action.new_network
        if nic.port:
            if network:
                network_map[nic.port.label] = network.network_id
            else:
                network_map[nic.port.label] = None
        else:
            logging.getLogger(__name__).warn(
                'Not modifying NIC %s; NIC is not on a port.' %
                nic.label)

    # Apply them
    driver_name = config.cfg.get('general', 'driver')
    driver = importlib.import_module('haas.drivers.' + driver_name)
    driver.apply_networking(network_map)

    # Then perform the database change and delete them
    for action in actions:
        action.nic.network = action.new_network
        db.delete(action)

    db.commit()
    return True
