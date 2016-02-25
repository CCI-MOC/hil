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
"""core database objects for the HaaS"""

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, sessionmaker,backref
from passlib.hash import sha512_crypt
from subprocess import call, check_call, Popen, PIPE
import subprocess
from haas.network_allocator import get_network_allocator
from haas.config import cfg
from haas.dev_support import no_dry_run
from haas.errors import OBMError
import uuid
import xml.etree.ElementTree
import logging
import os

Base=declarative_base()
Session = sessionmaker()

# A joining table for users and projects, which have a many to many relationship:
user_projects = Table('user_projects', Base.metadata,
                    Column('user_id', ForeignKey('user.id')),
                    Column('project_id', ForeignKey('project.id')))


def init_db(create=False, uri=None):
    """Start up the DB connection.

    If `create` is True, this will generate the schema for the database, and
    perform initial population of tables.

    `uri` is the uri to use for the databse. If it is None, the uri from the
    config file will be used.
    """

    if uri == None:
        uri = cfg.get('database', 'uri')

    engine = create_engine(uri)
    if create:
        Base.metadata.create_all(engine)
    Session.configure(bind=engine)
    if create:
        get_network_allocator().populate(Session())

class AnonModel(Base):
    """A database model with a primary key, 'id', but no user-visible label

    All our database models descend from this class.

    Its main purpose is to reduce boilerplate by doing things such as
    auto-generating table names.

    Extensions may inherit from this class to create new talbles.
    """
    __abstract__ = True
    id = Column(Integer, primary_key=True, nullable=False)

    def __repr__(self):
        return '%s<%r>' % (self.__class__.__name__, self.id)

    @declared_attr
    def __tablename__(cls):
        """Automatically generate the table name."""
        return cls.__name__.lower()


class Model(AnonModel):
    """A database model with a primary key 'id' and a user-visible label.

    All objects in the HaaS API are referenced by their 'label', so all such
    objects descend from this class.

    Extensions may inherit from this class to create new talbles.
    """
    __abstract__ = True
    label = Column(String, nullable=False)

    def __repr__(self):
        return '%s<%r>' % (self.__class__.__name__, self.label)


class Nic(Model):
    """a nic belonging to a Node"""

    # The Node to which the nic belongs:
    owner_id   = Column(ForeignKey('node.id'), nullable=False)
    owner     = relationship("Node",backref=backref('nics'))

    # The mac address of the nic:
    mac_addr  = Column(String)

    # The switch port to which the nic is attached:
    port_id   = Column(ForeignKey('port.id'))
    port      = relationship("Port",backref=backref('nic',uselist=False))

    def __init__(self, node, label, mac_addr):
        self.owner     = node
        self.label     = label
        self.mac_addr  = mac_addr


class Node(Model):
    """a (physical) machine"""

    # The project to which this node is allocated. If the project is null, the
    # node is unallocated:
    project_id    = Column(ForeignKey('project.id'))
    project       = relationship("Project",backref=backref('nodes'))

    # The Obm info is fetched from the obm class and its respective subclass
    # pertaining to the node 
    obm_id = Column(Integer, ForeignKey('obm.id'), nullable=False)
    obm = relationship("Obm", uselist=False, backref="node")


class Project(Model):
    """a collection of resources

    A project may contain allocated nodes, networks, and headnodes.
    """

    def __init__(self, label):
        """Create a project with the given label."""
        self.label = label


class Network(Model):
    """A link-layer network.

    See docs/networks.md for more information on the parameters.
    """

    # The project to which the network belongs, or None if the network was
    # created by the administrator.  This field determines who can delete a
    # network.
    creator_id = Column(ForeignKey('project.id'))
    creator    = relationship("Project",
                              backref=backref('networks_created'),
                              foreign_keys=[creator_id])
    # The project that has access to the network, or None if the network is
    # public.  This field determines who can connect a node or headnode to a
    # network.
    access_id = Column(ForeignKey('project.id'))
    access    = relationship("Project",
                             backref=backref('networks_access'),
                             foreign_keys=[access_id])
    # True if network_id was allocated by the driver; False if it was
    # assigned by an administrator.
    allocated = Column(Boolean)

    # An identifier meaningful to the networking driver:
    network_id    = Column(String, nullable=False)

    def __init__(self, creator, access, allocated, network_id, label):
        """Create a network.

        The network will belong to `project`, and have a symbolic name of
        `label`. `network_id`, as expected, is the identifier meaningful to
        the driver.
        """
        self.network_id = network_id
        self.creator = creator
        self.access = access
        self.allocated = allocated
        self.label = label


class Port(Model):
    """a port on a switch

    The port's label is an identifier that is meaningful only to the
    corresponding switch's driver.
    """
    owner_id = Column(ForeignKey('switch.id'), nullable=False)
    owner = relationship('Switch', backref=backref('ports'))

    def __init__(self, label, switch):
        """Register a port on a switch."""
        self.label = label
        self.owner = switch


class Switch(Model):
    """A network switch.

    This is meant to be subclassed by switch-specific drivers, implemented
    by extensions.

    Subclasses MUST override both ``validate`` and ``session``.
    """

    type = Column(String, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'switch',
        'polymorphic_on': type,
    }

    @staticmethod
    def validate(kwargs):
        """Verify that ``kwargs`` is a legal set of keyword args to ``__init__``

        Raise a ``schema.SchemaError`` if the ``kwargs`` is invalid.

        Note well: this is a *static* method; it will be invoked on the class.
        """
        assert False, "Subclasses MUST override the validate method"

    def session(self):
        """Return a session object for the switch.

        Conceputally, a session is an active connection to the switch; it lets
        HaaS avoid connecting and disconnecting for each change. the session
        object must have the methods:

            def apply_networking(self, action):
                '''Apply the NetworkingAction ``action`` to the switch.

                Action is guaranteed to reference a port object that is
                attached to the correct switch.
                '''

            def disconnect(self):
                '''Disconnect from the switch.

                This will be called when HaaS is done with the session.
                '''

            def get_port_networks(self, ports):
                '''Return a mapping from port objects to (channel, network ID) pairs.

                ``ports`` is a list of port objects to collect information on.

                The return value will be a dictionary of the form:

                    {
                        Port<"port-3">: [("vlan/native", "23"), ("vlan/52", "52")],
                        Port<"port-7">: [("vlan/23", "23")],
                        Port<"port-8">: [("vlan/native", "52")],
                        ...
                    }

                With one key for each element in the ``ports`` argument.

                This method is only for use by the test suite.
                '''

        Some drivers may do things that are not connection-oriented; If so,
        they can just return a dummy object here. The recommended way to
        handle this is to define the two methods above on the switch object,
        and have ``session`` just return ``self``.
        """

class Obm(AnonModel):
    """Obm superclass supporting various drivers 

    related to out of band management of servers.
    """
    type = Column(String, nullable=False)

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

    def power_cycle(self):
        """Power cycles the node.

        Exact implementation is left to the subclasses.
        """     
        assert False, "Subclasses MUST override the power_cycle method "
    
    def power_off(self):
	""" Shuts off the node.

	Exact implementation is left to the subclasses. 
	"""
	
	assert False, "Subclasses MUST override the power_off method "
    
    def start_console(self):
        """Starts logging to the console. """
        assert False, "Subclasses MUST override the start_console method" 

    def stop_console(self):
        """Stops console logging. """
        assert False, "Subclasses MUST override the stop_console method"

    def delete_console(self):
        assert False, "Subclasses MUST override the delete_console method"

    def get_console(self):
        assert False, "Subclasses MUST override the get_console method"

    def get_console_log_filename(self):
        assert False, "Subclasses MUST override the get_console_log_filename method"


class User(Model):
    """A user of the HaaS.

    Right now we're not doing authentication, so this isn't really used. In
    theory, a user must autheticate, and their membership within projects
    determines what they are authorized to do.
    """

    # The user's salted & hashed password. We currently use sha512 as the
    # hashing algorithm:
    hashed_password = Column(String)

    # The projects of which the user is a member.
    projects = relationship('Project', secondary = user_projects, backref = 'users')

    def __init__(self, label, password):
        """Create a user `label` with the specified (plaintext) password."""
        self.label = label
        self.set_password(password)

    def verify_password(self, password):
        """Return whether `password` is the user's (plaintext) password."""
        return sha512_crypt.verify(password, self.hashed_password)

    def set_password(self, password):
        """Set the user's password to `password` (which must be plaintext)."""
        self.hashed_password = sha512_crypt.encrypt(password)


def _on_virt_uri(args_list):
    """Make an argument list to libvirt tools use right URI.

    This will work for virt-clone and virsh, at least.  It gets the
    appropriate endpoint URI from the config file.
    """
    libvirt_endpoint = cfg.get('headnode', 'libvirt_endpoint')
    return [args_list[0], '--connect', libvirt_endpoint] + args_list[1:]


class Headnode(Model):
    """A virtual machine used to administer a project."""

    # The project to which this Headnode belongs:
    project_id = Column(ForeignKey('project.id'), nullable=False)
    project = relationship("Project", backref=backref('headnodes', uselist=True))

    # True iff there are unapplied changes to the Headnode:
    dirty = Column(Boolean, nullable=False)
    base_img = Column(String, nullable=False)

    # We need a guaranteed unique name to generate the libvirt machine name;
    # The name is therefore a function of a uuid:
    uuid = Column(String, nullable=False, unique=True)

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
        check_call(_on_virt_uri(['virsh', 'autostart', '--disable', self._vmname()]))

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


class Hnic(Model):
    """a network interface for a Headnode"""

    # The Headnode to which this Hnic belongs:
    owner_id    = Column(ForeignKey('headnode.id'), nullable=False)
    owner       = relationship("Headnode", backref = backref('hnics'))

    # The network to which this Hnic is attached.
    network_id  = Column(ForeignKey('network.id'))
    network     = relationship("Network", backref=backref('hnics'))

    def __init__(self, headnode, label):
        """Create an Hnic attached to the given headnode. with the given label."""
        self.owner    = headnode
        self.label    = label

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


class NetworkingAction(AnonModel):
    """A journal entry representing a pending networking change."""

    # This model is not visible in the API, so inherit from AnonModel

    nic_id         = Column(ForeignKey('nic.id'), nullable=False)
    new_network_id = Column(ForeignKey('network.id'), nullable=True)
    channel        = Column(String, nullable=False)

    nic = relationship("Nic", backref=backref('current_action', uselist=False))
    new_network = relationship("Network",
                               backref=backref('scheduled_nics',
                                               uselist=True))


class NetworkAttachment(AnonModel):
    """An attachment of a network to a particular nic on a channel"""
    # TODO: it would be nice to place explicit unique constraints on some
    # things:
    #
    # * (nic_id, network_id)
    # * (nic_id, channel)
    nic_id     = Column(ForeignKey('nic.id'),     nullable=False)
    network_id = Column(ForeignKey('network.id'), nullable=False)
    channel    = Column(String, nullable=False)

    nic     = relationship('Nic', backref=backref('attachments'))
    network = relationship('Network', backref=backref('attachments'))
