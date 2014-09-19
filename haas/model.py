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

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, sessionmaker,backref
from passlib.hash import sha512_crypt
from subprocess import call, check_call
import subprocess
from haas.config import cfg
from haas.dev_support import no_dry_run
import importlib
import uuid
import xml.etree.ElementTree
import logging

Base=declarative_base()
Session = sessionmaker()

user_groups = Table('user_groups', Base.metadata,
                    Column('user_id', Integer, ForeignKey('user.id')),
                    Column('group_id', Integer, ForeignKey('group.id')))


def init_db(create=False, uri=None):
    """Start up the DB connection.
    create: Pushes a new schema to your DB
    uri:    DB connection URI. If "None", pull from the config file
    """

    if uri == None:
        uri = cfg.get('database', 'uri')

    driver_name = cfg.get('general', 'driver')
    driver = importlib.import_module('haas.drivers.' + driver_name)

    engine = create_engine(uri)
    if create:
        Base.metadata.create_all(engine)
    Session.configure(bind=engine)

    driver.init_db(create=create)


class Model(Base):
    """All of our database models are descendants of this class.

    Its main purpose is to reduce boilerplate by doing things such as
    auto-generating table names.
    """
    __abstract__ = True
    id = Column(Integer, primary_key=True, nullable=False)
    label = Column(String, nullable=False)

    def __repr__(self):
        return '%s<%r>' % (self.__class__.__name__, self.label)

    @declared_attr
    def __tablename__(cls):
        """Automatically generate the table name."""
        return cls.__name__.lower()


class Nic(Model):
    mac_addr  = Column(String)

    owner_id   = Column(Integer,ForeignKey('node.id'), nullable=False)
    owner     = relationship("Node",backref=backref('nics'))
    port_id   = Column(Integer,ForeignKey('port.id'))
    port      = relationship("Port",backref=backref('nic',uselist=False))
    network_id = Column(Integer, ForeignKey('network.id'))
    network   = relationship("Network", backref=backref('nics'))

    def __init__(self, node, label, mac_addr):
        self.owner     = node
        self.label     = label
        self.mac_addr  = mac_addr


class Node(Model):
    project_id    = Column(Integer,ForeignKey('project.id'))
    #many to one mapping to project
    project       = relationship("Project",backref=backref('nodes'))

    ipmi_host = Column(String, nullable=False)
    ipmi_user = Column(String, nullable=False)
    ipmi_pass = Column(String, nullable=False)

    def __init__(self, label, ipmi_host, ipmi_user, ipmi_pass):
        self.label = label
        self.ipmi_host = ipmi_host
        self.ipmi_user = ipmi_user
        self.ipmi_pass = ipmi_pass

    def _ipmitool(self, args):
        """Invoke ipmitool with the right host/pass etc. for this node.

        `args` - any additional arguments to pass to ipmitool.
        """
        status = call(['ipmitool',
            '-U', self.ipmi_user,
            '-P', self.ipmi_pass,
            '-H', self.ipmi_host] + args)
        if status != 0:
            logger = logging.getLogger(__name__)
            logger.info('Nonzero exit status from ipmitool, args = %r', args)
        return status
            

    def power_cycle(self):
        self._ipmitool(['chassis', 'bootdev', 'pxe'])
        status = self._ipmitool(['chassis', 'power', 'cycle'])
        if status != 0:
            # power cycle will fail if the machine isn't running, so let's
            # just turn it on in that case. This way we can save power by
            # turning things off without breaking the HaaS. 
            status = self._ipmitool(['chassis', 'power', 'on'])
        return status == 0


class Project(Model):
    dirty = Column(Boolean, nullable=False)

    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    group = relationship("Group", backref=backref("projects"))

    def __init__(self, group, label):
        self.group = group
        self.label = label
        self.dirty = False


class Network(Model):
    """A link-layer network."""

    project_id    = Column(String,ForeignKey('project.id'), nullable=False)
    project = relationship("Project",backref=backref('networks'))

    network_id    = Column(String, nullable=False)

    def __init__(self, project, network_id, label):
        self.network_id = network_id
        self.project = project
        self.label = label



class Port(Model):
    owner_id     = Column(String,ForeignKey('switch.id'), nullable=False)
    owner        = relationship("Switch",backref=backref('ports'))

    def __init__(self, switch, label):
        self.owner = switch
        self.label   = label



class Switch(Model):
    driver = Column(String)

    def __init__(self, label, driver):
        self.label = label
        self.driver = driver


class User(Model):
    hashed_password    = Column(String)

    groups      = relationship('Group', secondary = user_groups, backref = 'users')

    def __init__(self, label, password):
        self.label = label
        self.set_password(password)

    def verify_password(self, password):
        return sha512_crypt.verify(password, self.hashed_password)

    def set_password(self, password):
        self.hashed_password = sha512_crypt.encrypt(password)


class Group(Model):

    def __init__(self, label):
        self.label = label


class Headnode(Model):
    project_id = Column(String, ForeignKey('project.id'), nullable=False)
    project = relationship("Project", backref=backref('headnode', uselist=True))
    dirty = Column(Boolean, nullable=False)

    # We need a guaranteed unique name to generate the libvirt machine name
    uuid = Column(String, nullable=False, unique=True)

    def __init__(self, project, label):
        self.project = project
        self.label = label
        self.dirty = True
        self.uuid = str(uuid.uuid1())

    @no_dry_run
    def create(self):
        """Creates the vm within libvirt, by cloning the base image.

        The vm is not started at this time.
        """
        # Before doing anything else, make sure the VM doesn't already
        # exist. This gives us the nice property that create will not fail
        # because of state left behind by previous failures (much like
        # applying a project):
        call(['virsh', 'undefine', self._vmname(), '--remove-all-storage'])
        # The --remove-all-storage flag above *should* take care of this,
        # but doesn't seem to on our development setup. XXX.
        call(['rm', '-f', '/var/lib/libvirt/images/%s.img' % self._vmname()])

        check_call(['virt-clone', '-o', 'base-headnode', '-n', self._vmname(), '--auto-clone'])
        for hnic in self.hnics:
            hnic.create()

    def delete(self):
        """Delete the vm, including associated storage"""
        # XXX: This doesn't actually work. I copied this from the headnode
        # module so I could finally delete it, but I haven't actually made the
        # slight changes needed to get it to work again (variable renames,
        # mostly).
        cmd(['virsh', 'undefine', self.name, '--remove-all-storage'])

    @no_dry_run
    def start(self):
        """Powers on the vm, which must have been previously created.

        Once the headnode has been started once it is "frozen," and no changes
        may be made to it, other than starting, stopping or deleting it.
        """
        check_call(['virsh', 'start', self._vmname()])
        self.dirty = False

    @no_dry_run
    def stop(self):
        """Stop the vm.

        This does a hard poweroff; the OS is not given a chance to react.
        """
        check_call(['virsh', 'destroy', self._vmname()])

    def _vmname(self):
        """Returns the name (as recognized by libvirt) of this vm."""
        return 'headnode-%s' % self.uuid


    # This function returns a meaningful value, but also uses actual hardware.
    # It has no_dry_run because the unit test for 'show_headnode' will call
    # it.  None is a fine return value there, because it will just put it into
    # a JSON object.
    @no_dry_run
    def get_vncport(self):
        """Returns the port that VNC is listening on, as an int.

        If the VM is off, in all likelihood the result will be None.  This is
        because no port has been allocated to it yet.  (The XML will also have
        "autoport='yes'".)

        If the VM has not been created yet (and is therefore dirty), return
        None.
        """
        if self.dirty:
            return None

        p = subprocess.Popen(['virsh', 'dumpxml', self._vmname()],
                             stdout=subprocess.PIPE)
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
    owner_id    = Column(Integer, ForeignKey('headnode.id'), nullable=False)
    owner       = relationship("Headnode", backref = backref('hnics'))

    mac_addr    = Column(String)

    network_id  = Column(Integer, ForeignKey('network.id'))
    network     = relationship("Network", backref=backref('hnics'))

    def __init__(self, headnode, label, mac_addr):
        self.owner    = headnode
        self.label    = label
        self.mac_addr = mac_addr

    @no_dry_run
    def create(self):
        if not self.network:
            # It is non-trivial to make a NIC not connected to a network, so
            # do nothing at all instead.
            return
        vlan_no = str(self.network.network_id)
        bridge = 'br-vlan%s' % vlan_no
        check_call(['virsh', 'attach-interface', self.owner._vmname(), 'bridge', bridge, '--config'])
