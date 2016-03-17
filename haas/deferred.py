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

from haas import model
import logging

def apply_networking():
    """Do each networking action in the journal, then cross them off.

    Returns False if the journal was empty, and True if there were journal
    entries.  Equivalently, returns True if an action was performed, and False
    if no action was performed.

    The networking server calls this function in a loop, to ensure that all
    pending network operations get processed within a reasonable amount of
    time.  The return value from this function lets the server know whether it
    should check for new journal entries, or if it should wait.  If this
    function does work, the server should immediately check again, because new
    entries might have been added in the meantime.  But, if this function
    returns immediately, the server should sleep, because there was no time
    for new entries to be added.  This keeps the networking server from
    tight-looping.
    """
    db = model.Session()

    # Get the journal entries
    actions = db.query(model.NetworkingAction).\
        order_by(model.NetworkingAction.id).all()

    switch_sessions = {}

    if actions == []:
        # No actions to perform.  Return False immediately.
        db.commit()
        return False

    for action in actions:
        nic = action.nic
        network = action.new_network
        if nic.port:
            if network:
                network_id = network.network_id
            else:
                network_id = None

            switch = nic.port.owner
            if switch.label not in switch_sessions:
                switch_sessions[switch.label] = switch.session()
            switch_sessions[switch.label].apply_networking(action)
        else:
            logging.getLogger(__name__).warn(
                'Not modifying NIC %s; NIC is not on a port.' %
                nic.label)

    # Close all of our sessions:
    for session in switch_sessions.values():
        session.disconnect()

    # Then perform the database changes and delete them
    for action in actions:
        if action.new_network is None:
            db.query(model.NetworkAttachment)\
                .filter_by(nic=action.nic, channel=action.channel)\
                .delete()
        else:
            db.add(model.NetworkAttachment(nic=action.nic,
                                           network=action.new_network,
                                           channel=action.channel))
        db.delete(action)

    db.commit()
    return True
