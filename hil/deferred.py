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
    """A daemon session tracks switch sessions during a call to
    apply_networking, and applies networking actions.

    When applying a networking action, if the DaemonSession does not
    already have a switch session for the relevant switch, it will
    create one, and cache it for next time.
    """

    def __init__(self):
        self.switch_sessions = {}

    def handle_action(self, action):
        """apply the networking action ``action``."""
        if action.type not in model.NetworkingAction.legal_types:
            logger.warn('Illegal action type %r from server; ignoring.')
        elif not action.nic.port:
            logger.warn('Not modifying NIC %s; NIC is not on a port.',
                        action.nic.label)
        else:
            getattr(self, action.type)(action)

    def modify_port(self, action):
        """Apply a modify_port action."""
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
        """Apply a revert_port action."""
        session = self.get_session(action.nic.port.owner)
        session.revert_port(action.nic.port.label)
        model.NetworkAttachment.query.filter_by(nic=action.nic).delete()

    def get_session(self, switch):
        """Get a session for the switch.

        If we don't already have one, create a new one and cache it. Otherwise,
        return the cached session.
        """
        if switch.label not in self.switch_sessions:
            self.switch_sessions[switch.label] = switch.session()
        return self.switch_sessions[switch.label]

    def close(self):
        """Shut down all of the open switch sessions."""
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
    should check for new journal entries immediately, or if it should wait.  If
    this function does work, the server should immediately check again, because
    new entries might have been added in the meantime.  But, if this function
    returns immediately, the server should sleep, because there was no time for
    new entries to be added.  This keeps the networking server from
    tight-looping.
    """

    action = model.NetworkingAction.query \
        .order_by(model.NetworkingAction.id).first()
    if action is None:
        db.session.commit()
        return False

    session = DaemonSession()
    while action is not None:
        session.handle_action(action)
        db.session.delete(action)
        db.session.commit()
        # Get the next action
        action = model.NetworkingAction.query \
            .order_by(model.NetworkingAction.id).first()

    # the last statement in the while loop opens a new db session that we must
    # close when we exit the loop.
    db.session.commit()

    session.close()
    return True
