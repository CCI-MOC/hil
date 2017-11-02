# Copyright 2016 Massachusetts Open Cloud Contributors
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

'''Functional test for deferred.py'''

import pytest
import tempfile

from hil import config, deferred, model
from hil.model import db, Switch
from hil.test_common import config_testsuite, config_merge, \
                             fresh_database, fail_on_log_warnings
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)
fresh_database = pytest.fixture(fresh_database)

DeferredTestSwitch = None


class RevertPortError(Exception):
    """An exception thrown by the switch implementation's revert_port.

    This is used as part of the error handling tests.
    """


def new_db():
    """ returns a new database connection"""
    local_app = Flask(__name__.split('.')[0])
    uri = config.cfg.get('database', 'uri')
    local_app.config.update(SQLALCHEMY_TRACK_MODIFICATIONS=False)
    local_app.config.update(SQLALCHEMY_DATABASE_URI=uri)
    local_db = SQLAlchemy(local_app)
    return local_db


@pytest.fixture
def configure():
    """Configure HIL.

    The tests in this module require two separate sessions, so if the
    configuration specifies an in-memory sqlite database, we use a
    temporary file instead.
    """
    config_testsuite()

    additional_config = {
        'extensions': {
            'hil.ext.obm.mock': ''
            }
        }

    # if we are using sqlite's in memory db, then change uri to a db on disk
    uri = config.cfg.get('database', 'uri')
    if uri == 'sqlite:///:memory:':
        with tempfile.NamedTemporaryFile() as temp_db:
            uri = 'sqlite:///' + temp_db.name
            additional_config['database'] = {'uri': uri}
            config_merge(additional_config)
            config.load_extensions()
            yield
    else:
        config_merge(additional_config)
        config.load_extensions()
        yield


@pytest.fixture()
def _deferred_test_switch_class():
    global DeferredTestSwitch

    class DeferredTestSwitch_(Switch):
        '''DeferredTestSwitch

        This is a switch implemented to test the deferred.apply_networking()
        function.  It is needed for a custom implementation of the switch's
        apply_networking() that counts the networking actions as
        apply_networking() is called to ensure it is incremental.

        It is defined as a fixture because if it is defined as a class with
        global scope it's going to be defined for every test; so this will be
        picked up by migration tests and those would fail because there will be
        no migration scripts for this switch's table.
        '''

        api_name = 'http://schema.massopencloud.org/haas/v0/switches/deferred'

        __mapper_args__ = {
            'polymorphic_identity': api_name,
        }

        id = db.Column(db.Integer,
                       db.ForeignKey('switch.id'),
                       primary_key=True)
        hostname = db.Column(db.String, nullable=False)
        username = db.Column(db.String, nullable=False)
        password = db.Column(db.String, nullable=False)
        last_count = None

        @staticmethod
        def validate(kwargs):
            """Implement Switch.validate.

            This currently doesn't check anything; in theory we should validate
            that the arguments are sane, but right now aren't worrying about it
            since this method is only called from the API server, and we never
            use this switch type there.
            """

        def session(self):
            """Return a switch session.

            This just returns self, since there's no connection to speak of.
            """
            return self

        def disconnect(self):
            """Implement the session's disconnect() method.

            This is a no-op, since session() doesn't establish a connection.
            """

        def modify_port(self, port, channel, network_id):
            """Implement Switch.modify_port.

            This implementation keeps track of how many pending
            NetworkingActions there are, and fails the test if apply_networking
            calls it without committing the previous change.
            """
            # get a new connection to database so that this method does
            # not see uncommited changes by `apply_networking`
            local_db = new_db()
            current_count = local_db.session \
                .query(model.NetworkingAction).count()

            local_db.session.commit()
            local_db.session.close()

            if self.last_count is None:
                self.last_count = current_count
            else:
                assert current_count == self.last_count - 1, \
                  "network daemon did not commit previous change!"
                self.last_count = current_count

        def revert_port(self, port):
            """Implement Switch.revert_port.

            This always fails, which the tests rely on to check
            error handling behavior.
            """
            raise RevertPortError('revert_port always fails.')

    DeferredTestSwitch_.__name__ = 'DeferredTestSwitch'
    DeferredTestSwitch = DeferredTestSwitch_


@pytest.fixture()
def switch(_deferred_test_switch_class):
    """Get an instance of DeferredTestSwitch."""
    return DeferredTestSwitch(
        label='switch',
        hostname='http://example.com',
        username='admin',
        password='admin',
    )


def new_nic(name):
    """Create a new nic named ``name``, and an associated Node + Obm."""
    from hil.ext.obm.mock import MockObm
    return model.Nic(
        model.Node(
            label='node-99',
            obm=MockObm(
                type="http://schema.massopencloud.org/haas/v0/obm/mock",
                host="ipmihost",
                user="root",
                password="tapeworm")),
        name,
        '00:11:22:33:44:55')


@pytest.fixture()
def network():
    """Create a test network (and associated project) to work with."""
    project = model.Project('anvil-nextgen')
    return model.Network(project, [project], True, '102', 'hammernet')

pytestmark = pytest.mark.usefixtures('configure',
                                     'fail_on_log_warnings')


def test_apply_networking(switch, network, fresh_database):
    '''Test to validate apply_networking commits actions incrementally

    This test verifies that the apply_networking() function in hil/deferred.py
    incrementally commits actions, which ensures that any error on an action
    will not require a complete rerun of the prior actions (e.g. if an error
    is thrown on the 3rd action, the 1st and 2nd action will have already been
    committed)

    The test also verifies that if a new networking action fails, then the
    old networking actions in the queue were commited.
    '''
    nic = []
    actions = []
    # initialize 3 nics and networking actions
    for i in range(0, 3):
        interface = 'gi1/0/%d' % (i)
        nic.append(new_nic(str(i)))
        nic[i].port = model.Port(label=interface, switch=switch)
        actions.append(model.NetworkingAction(nic=nic[i], new_network=network,
                                              channel='vlan/native',
                                              type='modify_port'))

    # this makes the last action invalid for the test switch because the switch
    # raises an error when the networking action is of type revert port.
    actions[2] = model.NetworkingAction(nic=nic[2],
                                        new_network=None,
                                        channel='',
                                        type='revert_port')
    for action in actions:
        db.session.add(action)
    db.session.commit()

    with pytest.raises(RevertPortError):
        deferred.apply_networking()

    # close the session opened by `apply_networking` when `handle_actions`
    # fails; without this the tests would just stall (when using postgres)
    db.session.close()

    local_db = new_db()

    pending_action = local_db.session \
        .query(model.NetworkingAction) \
        .order_by(model.NetworkingAction.id).one_or_none()
    current_count = local_db.session \
        .query(model.NetworkingAction).count()

    local_db.session.delete(pending_action)
    local_db.session.commit()
    local_db.session.close()

    # test that there's only pending action in the queue and it is of type
    # revert_port
    assert current_count == 1
    assert pending_action.type == 'revert_port'
