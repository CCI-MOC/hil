'''Functional test for deferred.py'''

import pytest
import tempfile
import uuid

from hil import config, deferred, model, api
from hil.model import db, Switch
from hil.errors import SwitchError
from hil.test_common import config_testsuite, config_merge, \
                             fresh_database
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

fresh_database = pytest.fixture(fresh_database)

DeferredTestSwitch = None


class RevertPortError(SwitchError):
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

    # if we are using sqlite's in memory db, then change uri to a db on disk
    uri = config.cfg.get('database', 'uri')
    if uri == 'sqlite:///:memory:':
        with tempfile.NamedTemporaryFile() as temp_db:
            uri = 'sqlite:///' + temp_db.name
            config_merge({
                'database': {
                    'uri': uri
                },
            })
            config.load_extensions()
            yield
    else:
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
                .query(model.NetworkingAction).filter_by(status='PENDING') \
                .count()

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
    """Create a new nic named ``name``, and an associated Node + Obm.
    The new nic is attached to a new node each time, and the node is added to
    the project named 'anvil-nextgen-####' """

    unique_id = str(uuid.uuid4())
    project = model.Project('anvil-nextgen-' + unique_id)
    label = str(uuid.uuid4())
    node = model.Node(
        label=label,
        obmd_uri='http://obmd.example.com/nodes/' + label,
        obmd_admin_token='secret',
    )
    if node.project is None:
        project.nodes.append(node)
    return model.Nic(node, name, '00:11:22:33:44:55')


@pytest.fixture()
def network():
    """Create a test network (and associated project) to work with."""
    project = model.Project('anvil-nextgen')
    return model.Network(project, [], True, '102', 'hammernet')


pytestmark = pytest.mark.usefixtures('configure')


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
    for i in range(0, 2):
        interface = 'gi1/0/%d' % (i)
        nic.append(new_nic(str(i)))
        nic[i].port = model.Port(label=interface, switch=switch)
        unique_id = str(uuid.uuid4())
        actions.append(model.NetworkingAction(nic=nic[i],
                                              new_network=network,
                                              channel='vlan/native',
                                              type='modify_port',
                                              uuid=unique_id,
                                              status='PENDING'))

    # Create another aciton of type revert_port. This action is invalid for the
    # test switch because the switch raises an error when the networking action
    # is of type revert port.
    unique_id = str(uuid.uuid4())
    nic.append(new_nic('2'))
    nic[2].port = model.Port(label=interface, switch=switch)
    actions.append(model.NetworkingAction(nic=nic[2],
                                          new_network=None,
                                          uuid=unique_id,
                                          channel='',
                                          status='PENDING',
                                          type='revert_port'))

    # get some nic attributes before we close this db session.
    nic2_label = nic[2].label
    nic2_node = nic[2].owner.label

    for action in actions:
        db.session.add(action)
    db.session.commit()

    # simple check to ensure that right number of actions are added.
    total_count = db.session.query(model.NetworkingAction).count()
    assert total_count == 3

    deferred.apply_networking()

    # close the session opened by `apply_networking` when `handle_actions`
    # fails; without this the tests would just stall (when using postgres)
    db.session.close()

    local_db = new_db()

    errored_action = local_db.session \
        .query(model.NetworkingAction) \
        .order_by(model.NetworkingAction.id).filter_by(status='ERROR') \
        .one_or_none()

    # Count the number of actions with different statuses
    error_count = local_db.session \
        .query(model.NetworkingAction).filter_by(status='ERROR').count()

    pending_count = local_db.session \
        .query(model.NetworkingAction).filter_by(status='PENDING').count()

    done_count = local_db.session \
        .query(model.NetworkingAction).filter_by(status='DONE').count()

    # test that there's only 1 action that errored out in the queue and that it
    # is of type revert_port
    assert error_count == 1
    assert errored_action.type == 'revert_port'

    assert pending_count == 0
    assert done_count == 2
    local_db.session.commit()
    local_db.session.close()

    # add another action on a nic with a previously failed action.
    api.network_create('corsair', 'admin', '', '105')
    api.node_connect_network(nic2_node, nic2_label, 'corsair')

    # the api call should delete the errored action on that nic, and a new
    # pending action should appear.
    local_db = new_db()
    errored_action = local_db.session \
        .query(model.NetworkingAction) \
        .order_by(model.NetworkingAction.id).filter_by(status='ERROR') \
        .one_or_none()

    pending_action = local_db.session \
        .query(model.NetworkingAction) \
        .order_by(model.NetworkingAction.id).filter_by(status='PENDING') \
        .one_or_none()

    assert errored_action is None
    assert pending_action is not None

    local_db.session.commit()
    local_db.session.close()
