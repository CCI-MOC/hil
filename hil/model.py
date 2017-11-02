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
"""Core database logic for HIL

This module defines a number of built-in database objects used by HIL.
In addition, it provides some general infrastructure for dealing with the
database.

Extensions are permitted to create new database objects by subclassing from
`db.Model`.
"""

# from sqlalchemy import *
# from sqlalchemy.ext.declarative import declarative_base, declared_attr
# from sqlalchemy.orm import relationship, sessionmaker,backref
from flask.ext.sqlalchemy import SQLAlchemy
from subprocess import call, check_call, Popen, PIPE
from hil.flaskapp import app
from hil.config import cfg
from hil.dev_support import no_dry_run
import uuid
import xml.etree.ElementTree
from sqlalchemy import BigInteger
from sqlalchemy.dialects import sqlite

# without setting this explicitly, we get a warning that this option
# will default to disabled in future versions (due to incurring a lot
# of overhed). We aren't using the relevant functionality, so let's
# just opt-in to the change now:
app.config.update(SQLALCHEMY_TRACK_MODIFICATIONS=False)

db = SQLAlchemy(app)

# Sets up variant type so that postgresql can use BIGINT primary keys
# while sqlite uses Integer primary keys.
BigIntegerType = BigInteger().with_variant(
        sqlite.INTEGER(), 'sqlite')


def init_db(uri=None):
    """Start up the DB connection.

    `uri` is the uri to use for the database. If it is None, the uri from the
    config file will be used.
    """
    if uri is None:
        uri = cfg.get('database', 'uri')
    app.config.update(SQLALCHEMY_DATABASE_URI=uri)


# A joining table for project's access to networks, which have a many to many
# relationship:
network_projects = db.Table(
    'network_projects',
    db.Column('project_id', db.ForeignKey('project.id')),
    db.Column('network_id', db.ForeignKey('network.id')))


class Nic(db.Model):
    """a nic belonging to a Node"""

    id = db.Column(BigIntegerType, primary_key=True)
    label = db.Column(db.String, nullable=False)

    # The Node to which the nic belongs:
    owner_id = db.Column(db.ForeignKey('node.id'), nullable=False)
    owner = db.relationship("Node", backref=db.backref('nics'))

    # The mac address of the nic:
    mac_addr = db.Column(db.String)

    # The switch port to which the nic is attached:
    port_id = db.Column(db.ForeignKey('port.id'))
    port = db.relationship("Port",
                           backref=db.backref('nic', uselist=False))

    def __init__(self, node, label, mac_addr):
        self.owner = node
        self.label = label
        self.mac_addr = mac_addr


class Node(db.Model):
    """a (physical) machine"""
    id = db.Column(BigIntegerType, primary_key=True)
    label = db.Column(db.String, nullable=False)

    # The project to which this node is allocated. If the project is null, the
    # node is unallocated:
    project_id = db.Column(db.ForeignKey('project.id'))
    project = db.relationship("Project", backref=db.backref('nodes'))

    # The Obm info is fetched from the obm class and its respective subclass
    # pertaining to the node
    obm_id = db.Column(BigIntegerType, db.ForeignKey('obm.id'), nullable=False)
    obm = db.relationship("Obm",
                          uselist=False,
                          backref="node",
                          single_parent=True,
                          cascade='all, delete-orphan')


class Project(db.Model):
    """a collection of resources

    A project may contain allocated nodes, networks, and headnodes.
    """
    id = db.Column(BigIntegerType, primary_key=True)
    label = db.Column(db.String, nullable=False)

    def __init__(self, label):
        """Create a project with the given label."""
        self.label = label


class Metadata(db.Model):
    """metadata for a Node

    Metadata may a key, a hash, or otherwise
    """
    id = db.Column(BigIntegerType, primary_key=True)
    label = db.Column(db.String, nullable=False)
    value = db.Column(db.String)
    owner_id = db.Column(db.ForeignKey('node.id'), nullable=False)
    owner = db.relationship('Node', backref=db.backref('metadata'))

    def __init__(self, label, value, node):
        """Create a key with the given label."""
        self.label = label
        self.value = value
        self.owner = node


class Network(db.Model):
    """A link-layer network.

    See docs/networks.md for more information on the parameters.
    """
    id = db.Column(BigIntegerType, primary_key=True)
    label = db.Column(db.String, nullable=False)

    # The project to which the network belongs, or None if the network was
    # created by the administrator.  This field determines who can delete a
    # network.
    owner_id = db.Column(db.ForeignKey('project.id'))
    owner = db.relationship("Project",
                            backref=db.backref('networks_created'),
                            foreign_keys=[owner_id])
    # The project that has access to the network, or None if the network is
    # public.  This field determines who can connect a node or headnode to a
    # network.
    access = db.relationship("Project",
                             backref=db.backref('networks_access'),
                             secondary='network_projects')
    # True if network_id was allocated by the driver; False if it was
    # assigned by an administrator.
    allocated = db.Column(db.Boolean)

    # An identifier meaningful to the networking driver:
    network_id = db.Column(db.String, nullable=False)

    def __init__(self, owner, access, allocated, network_id, label):
        """Create a network.

        The network will belong to `project`, and have a symbolic name of
        `label`. `network_id`, as expected, is the identifier meaningful to
        the driver.
        """
        self.network_id = network_id
        self.owner = owner
        self.access = access
        self.allocated = allocated
        self.label = label


class Port(db.Model):
    """a port on a switch

    The port's label is an identifier that is meaningful only to the
    corresponding switch's driver.
    """
    id = db.Column(BigIntegerType, primary_key=True)
    label = db.Column(db.String, nullable=False)
    owner_id = db.Column(db.ForeignKey('switch.id'), nullable=False)
    owner = db.relationship('Switch', backref=db.backref('ports'))

    def __init__(self, label, switch):
        """Register a port on a switch."""
        self.label = label
        self.owner = switch


class Switch(db.Model):
    """A network switch.

    This is meant to be subclassed by switch-specific drivers, implemented
    by extensions.

    Subclasses MUST override both ``validate`` and ``session``.
    """
    id = db.Column(BigIntegerType, primary_key=True)
    label = db.Column(db.String, nullable=False)

    type = db.Column(db.String, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'switch',
        'polymorphic_on': type,
    }

    def validate_port_name(self, port):
        """Verify that port name is valid for switch"""

        assert False, "Subclasses MUST override the validate method"

    @staticmethod
    def validate(kwargs):
        """Verify that ``kwargs`` is a legal set of keyword args to ``__init__``

        Raise a ``schema.SchemaError`` if the ``kwargs`` is invalid.

        Note well: this is a *static* method; it will be invoked on the class.
        """
        assert False, "Subclasses MUST override the validate method"

    def session(self):
        """Return a session object for the switch.

        The returned object should satisfy the interface specified by
        SwitchSession, though it needn't actually subclass it.

        Some drivers may do things that are not connection-oriented; If so,
        they can just return a dummy object here. The recommended way to
        handle this is to define the methods above on the switch object,
        and have ``session`` just return ``self``.
        """

    def ensure_legal_operation(self, nic, op_type, channel):
        """Checks with the switch if the operation is legal before queueing it.

        channel is network channel
        nic is Nic object
        op_type is type of operation (connect, detach)

        Some drivers don't need this check at all. So the default behaviour is
        to just return"""

        return


class SwitchSession(object):
    """A session object for a switch.

    Conceptually, a session is an active connection to the switch; it lets
    HIL avoid connecting and disconnecting for each change.
    """

    def modify_port(self, port, channel, new_network):
        """Move the specified (port, channel) pair to new_network.

        `port` is the name of a port (`Port.label`) on the switch.

        `channel` is a channel identifier

        `new_network` is the network ID for the network to move to.
        If `new_network` is `None`, The (port, channel) pair should be
        removed from it's existing network (if any).
        """
        assert False, "Subclasses MUST override modify_port"

    def revert_port(self, port):
        """Detach the port from all networks.

        `port` is the name of a port (`Port.label`) on the switch.
        """
        assert False, "Subclasses MUST override revert_port"

    def disconnect(self):
        """Disconnect from the switch.

        This will be called when HIL is done with the session.
        """
        assert False, "Subclasses MUST override disconnect"

    def get_port_networks(self, ports):
        """Return a mapping from port objects to (channel, network ID)
            pairs.

        ``ports`` is a list of port objects to collect information on.

        The return value will be a dictionary of the form:

            {
                Port<"port-3">: [("vlan/native", "23"),
                                    ("vlan/52", "52")],
                Port<"port-7">: [("vlan/23", "23")],
                Port<"port-8">: [("vlan/native", "52")],
                ...
            }

        With one key for each element in the ``ports`` argument.

        This method is only for use by the test suite.
        """
        assert False, "Subclasses MUST override get_port_networks"


class Obm(db.Model):
    """Obm superclass supporting various drivers

    related to out of band management of servers.
    """
    id = db.Column(BigIntegerType, primary_key=True)
    type = db.Column(db.String, nullable=False)

    __mapper_args__ = {
        'polymorphic_on': type
    }

    @staticmethod
    def validate(kwargs):
        """Verify that ``kwargs`` is a legal set of keywords args to ``__init__``

        Raise a ``schema.SchemaError`` if the  ``kwargs`` is invalid.
        Note well: This is a *static* method; it will be invoked on the class.
        """
        assert False, "Subclasses MUST override the validate method "

    def power_cycle(self, force):
        """Power cycles the node.

        Exact implementation is left to the subclasses.

        ``force`` indicates that the node should be *forced* off, as opposed to
        e.g. given an ACPI shutdown signal, to which the node may respond.
        """
        assert False, "Subclasses MUST override the power_cycle method "

    def power_off(self):
        """ Shuts off the node.

        Exact implementation is left to the subclasses.
        """

        assert False, "Subclasses MUST override the power_off method "

    def require_legal_bootdev(self, dev):
        """Throws an exception upon invalid bootdev.

        Exact implementation is left to the subclasses.
        """
        assert False, "Subclasses MUST override the require_legal_bootdev" \
            "method"

    def set_bootdev(self, dev):
        """sets bootdevice to dev.

        Exact implementation is left to the subclasses.
        """
        assert False, "Subclasses MUST override the set_bootdev method "

    def start_console(self):
        """Starts logging to the console. """
        assert False, "Subclasses MUST override the start_console method"

    def stop_console(self):
        """Stops console logging. """
        assert False, "Subclasses MUST override the stop_console method"

    def delete_console(self):
        """Delete the console log."""
        assert False, "Subclasses MUST override the delete_console method"

    def get_console(self):
        """Return the contents of the console log."""
        assert False, "Subclasses MUST override the get_console method"

    def get_console_log_filename(self):
        """Return the name of the file containing the console log."""
        assert False, "Subclasses MUST override the get_console_log_filename" \
            "method"


def _on_virt_uri(args_list):
    """Make an argument list to libvirt tools use right URI.

    This will work for virt-clone and virsh, at least.  It gets the
    appropriate endpoint URI from the config file.
    """
    libvirt_endpoint = cfg.get('headnode', 'libvirt_endpoint')
    return [args_list[0], '--connect', libvirt_endpoint] + args_list[1:]


class Headnode(db.Model):
    """A virtual machine used to administer a project."""
    id = db.Column(BigIntegerType, primary_key=True)
    label = db.Column(db.String, nullable=False)

    # The project to which this Headnode belongs:
    project_id = db.Column(db.ForeignKey('project.id'), nullable=False)
    project = db.relationship(
        "Project", backref=db.backref('headnodes', uselist=True))

    # True iff there are unapplied changes to the Headnode:
    dirty = db.Column(db.Boolean, nullable=False)
    base_img = db.Column(db.String, nullable=False)

    # We need a guaranteed unique name to generate the libvirt machine name;
    # The name is therefore a function of a uuid:
    uuid = db.Column(db.String, nullable=False, unique=True)

    def __init__(self, project, label, base_img):
        """Create a headnode belonging to `project` with the given label."""
        self.project = project
        self.label = label
        self.dirty = True
        self.uuid = str(uuid.uuid1())
        self.base_img = base_img

    @no_dry_run
    def create(self):
        """Creates the vm within libvirt, by cloning the base image.

        The vm is not started at this time.
        """
        check_call(_on_virt_uri(['virt-clone',
                                 '-o', self.base_img,
                                 '-n', self._vmname(),
                                 '--auto-clone']))
        for hnic in self.hnics:
            hnic.create()

    @no_dry_run
    def delete(self):
        """Delete the vm, including associated storage"""
        # Don't check return value.  If the headnode was powered off, this
        # will fail, and we don't care.  If it fails for some other reason,
        # then the following line will also fail, and we'll catch that error.
        call(_on_virt_uri(['virsh', 'destroy', self._vmname()]))
        check_call(_on_virt_uri(['virsh',
                                 'undefine', self._vmname(),
                                 '--remove-all-storage']))

    @no_dry_run
    def start(self):
        """Powers on the vm, which must have been previously created.

        Once the headnode has been started once it is "frozen," and no changes
        may be made to it, other than starting, stopping or deleting it.
        """
        check_call(_on_virt_uri(['virsh', 'start', self._vmname()]))
        check_call(_on_virt_uri(['virsh', 'autostart', self._vmname()]))
        self.dirty = False

    @no_dry_run
    def stop(self):
        """Stop the vm.

        This does a hard poweroff; the OS is not given a chance to react.
        """
        check_call(_on_virt_uri(['virsh', 'destroy', self._vmname()]))
        check_call(_on_virt_uri(
            ['virsh', 'autostart', '--disable', self._vmname()]))

    def _vmname(self):
        """Returns the name (as recognized by libvirt) of this vm."""
        return 'headnode-%s' % self.uuid

    # This function returns a meaningful value, but also uses actual hardware.
    # It has no_dry_run because the unit test for 'show_headnode' will call
    # it.  None is a fine return value there, because it will just put it into
    # a JSON object.
    @no_dry_run
    def get_vncport(self):
        """Return the port that VNC is listening on, as an int.

        If the VM is powered off, the return value may be None -- this is
        dependant on the configuration of libvirt. A powered on VM will always
        have a vnc port.

        If the VM has not been created yet (and is therefore dirty) the return
        value will be None.
        """
        if self.dirty:
            return None

        p = Popen(_on_virt_uri(['virsh', 'dumpxml', self._vmname()]),
                  stdout=PIPE)
        xmldump, _ = p.communicate()
        root = xml.etree.ElementTree.fromstring(xmldump)
        port = root.findall("./devices/graphics")[0].get('port')
        if port == -1:
            # No port allocated (yet)
            return None
        else:
            return port
        # No VNC service found, so no port available
        return None


class Hnic(db.Model):
    """a network interface for a Headnode"""
    id = db.Column(BigIntegerType, primary_key=True)
    label = db.Column(db.String, nullable=False)

    # The Headnode to which this Hnic belongs:
    owner_id = db.Column(db.ForeignKey('headnode.id'), nullable=False)
    owner = db.relationship("Headnode", backref=db.backref('hnics'))

    # The network to which this Hnic is attached.
    network_id = db.Column(db.ForeignKey('network.id'))
    network = db.relationship("Network", backref=db.backref('hnics'))

    def __init__(self, headnode, label):
        """Create an Hnic attached to the given headnode. with the given
        label.
        """
        self.owner = headnode
        self.label = label

    @no_dry_run
    def create(self):
        """Create the hnic within livbirt.

        XXX: This is a noop if the Hnic isn't connected to a network. This
        means that the headnode won't have a corresponding nic, even a
        disconnected one.
        """
        if not self.network:
            # It is non-trivial to make a NIC not connected to a network, so
            # do nothing at all instead.
            return
        vlan_no = str(self.network.network_id)
        bridge = 'br-vlan%s' % vlan_no
        check_call(_on_virt_uri(['virsh',
                                 'attach-interface', self.owner._vmname(),
                                 'bridge', bridge,
                                 '--config']))


class NetworkingAction(db.Model):
    """A journal entry representing a pending networking change.

    This is basically an RPC call from the API server to the network daemon.
    Eventually we'll probably want to separate the storage for these daemons,
    at which point we can replace this with proper RPC.

    `legal_types` is a list of legal values for the `type` field. The meaning
    and relevance of the some other fields depends on the value of `type`; see
    the comments for each field.

    """

    # Legal values for `type`
    legal_types = ('modify_port', 'revert_port')

    id = db.Column(BigIntegerType, primary_key=True)

    # The type of action.
    #
    # * 'modify_port' attaches the (nic, channel) pair to a specified network,
    #    or detaches it from its existing network.
    # * 'revert_port' detaches the port from all networks.
    type = db.Column(db.String, nullable=False)

    nic_id = db.Column(db.ForeignKey('nic.id'), nullable=False)
    new_network_id = db.Column(db.ForeignKey('network.id'), nullable=True)

    # If `type` is 'modify_port', this denotes the channel that should be
    # affected on the given port. If `type` is 'revert_port', this field
    # is ignored.
    channel = db.Column(db.String, nullable=False)

    # The nic affected by the action. for 'revert_port', this is the nic
    # attached to the specified port.
    nic = db.relationship("Nic",
                          backref=db.backref('current_action', uselist=False))

    # For 'modify_port', this is the new network that the (nic, channel) pair
    # should be moved to, or None if the (nic, channel) should just be detached
    # from its current network.
    new_network = db.relationship("Network",
                                  backref=db.backref('scheduled_nics',
                                                     uselist=True))


class NetworkAttachment(db.Model):
    """An attachment of a network to a particular nic on a channel"""
    id = db.Column(BigIntegerType, primary_key=True)

    # TODO: it would be nice to place explicit unique constraints on some
    # things:
    #
    # * (nic_id, network_id)
    # * (nic_id, channel)
    nic_id = db.Column(db.ForeignKey('nic.id'), nullable=False)
    network_id = db.Column(db.ForeignKey('network.id'), nullable=False)
    channel = db.Column(db.String, nullable=False)

    nic = db.relationship('Nic', backref=db.backref('attachments'))
    network = db.relationship('Network', backref=db.backref('attachments'))
