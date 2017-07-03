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

from hil import model
from hil.model import db
import logging

logger = logging.getLogger(__name__)


class DaemonSession(object):

    def __init__(self):
        self.switch_sessions = {}

    def handle_action(self, action):
        if action.type not in model.NetworkingAction.legal_types:
            logger.warn('Illegal action type %r from server; ignoring.')
        elif not action.nic.port:
            logger.warn('Not modifying NIC %s; NIC is not on a port.',
                        action.nic.label)
        else:
            getattr(self, action.type)(action)

    def modify_port(self, action):
        session = self.get_session(action.nic.port.owner)

        if action.new_network is None:
            network_id = None
        else:
            network_id = action.new_network.network_id

        session.modify_port(action.nic.port.label,
                            action.channel,
                            network_id)
        if action.new_network is None:
            model.NetworkAttachment.query \
                .filter_by(nic=action.nic, channel=action.channel)\
                .delete()
        else:
            db.session.add(model.NetworkAttachment(
                nic=action.nic,
                network=action.new_network,
                channel=action.channel))

    def revert_port(self, action):
        session = self.get_session(action.nic.port.owner)
        session.revert_port(action.nic.port.label)
        model.NetworkAttachment.query.filter_by(nic=action.nic).delete()

    def get_session(self, switch):
        if switch.label not in self.switch_sessions:
            self.switch_sessions[switch.label] = switch.session()
        return self.switch_sessions[switch.label]

    def close(self):
        for session in self.switch_sessions.values():
            session.disconnect()
        self.switch_sessions = {}


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
    # Get the journal enries
    actions = model.NetworkingAction.query \
        .order_by(model.NetworkingAction.id).all()

    if actions == []:
        # No actions to perform.  Return False immediately.
        db.session.commit()
        return False

    session = DaemonSession()
    for action in actions:
        session.handle_action(action)
    session.close()
    model.NetworkingAction.query.delete()
    db.session.commit()
    return True
