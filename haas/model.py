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
from haas.config import cfg
from haas.dev_support import no_dry_run
import importlib

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

    driver_name = cfg.get('general', 'active_switch')
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

    port_id   = Column(Integer,ForeignKey('port.id'))
    node_id   = Column(Integer,ForeignKey('node.id'), nullable=False)
    network_id = Column(Integer, ForeignKey('network.id'))

    network   = relationship("Network", backref=backref('nics'))
    port      = relationship("Port",backref=backref('nic',uselist=False))
    node      = relationship("Node",backref=backref('nics'))

    def __init__(self, node, label, mac_addr):
        self.node      = node
        self.label     = label
        self.mac_addr  = mac_addr


class Node(Model):
    project_id    = Column(Integer,ForeignKey('project.id'))
    #many to one mapping to project
    project       = relationship("Project",backref=backref('nodes'))

    def __init__(self, label):
        self.label   = label


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
    network_id    = Column(String, nullable=False)

    project = relationship("Project",backref=backref('networks'))

    def __init__(self, project, network_id, label):
        self.network_id = network_id
        self.project = project
        self.label = label



class Port(Model):
    switch_id     = Column(Integer,ForeignKey('switch.id'), nullable=False)
    switch        = relationship("Switch",backref=backref('ports'))

    def __init__(self, switch, label):
        self.switch = switch
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
    project = relationship("Project", backref=backref('headnode', uselist=False))
    dirty = Column(Boolean, nullable=False)

    def __init__(self, project, label):
        self.project = project
        self.label = label
        self.dirty = True

    @no_dry_run
    def create(self):
        """Creates the vm within libvirt, by cloning the base image.

        The vm is not started at this time.
        """
        # Before doing anything else, make sure the VM doesn't already
        # exist. This gives us the nice property that create will not fail
        # because of state left behind by previous failures (much like
        # deploying a project):
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
        trunk_nic = cfg.get('headnode', 'trunk_nic')
        cmd(['virsh', 'undefine', self.name, '--remove-all-storage'])
        for nic in self.nics:
            nic = str(nic)
            bridge = 'br-vlan%s' % nic
            vlan_nic = '%s.%d' % (trunk_nic, nic)
            cmd(['ifconfig', bridge, 'down'])
            cmd(['ifconfig', vlan_nic, 'down'])
            cmd(['brctl', 'delif', bridge, vlan_nic])
            cmd(['vconfig', 'rem', vlan_nic])
            cmd(['brctl', 'delbr', bridge])


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
        return 'headnode-%d' % self.id


class Hnic(Model):
    mac_addr       = Column(String)
    headnode_id    = Column(Integer, ForeignKey('headnode.id'), nullable=False)
    network_id     = Column(Integer, ForeignKey('network.id'))

    headnode       = relationship("Headnode", backref = backref('hnics'))
    network        = relationship("Network", backref=backref('hnics'))

    def __init__(self, headnode, label, mac_addr):
        self.headnode = headnode
        self.label = label
        self.mac_addr = mac_addr

    @no_dry_run
    def create(self):
        trunk_nic = cfg.get('headnode', 'trunk_nic')
        vlan_no = str(self.network.network_id)
        bridge = 'br-vlan%s' % vlan_no
        vlan_nic = '%s.%s' % (trunk_nic, vlan_no)
        check_call(['brctl', 'addbr', bridge])
        check_call(['vconfig', 'add', trunk_nic, vlan_no])
        check_call(['brctl', 'addif', bridge, vlan_nic])
        check_call(['ifconfig', bridge, 'up', 'promisc'])
        check_call(['ifconfig', vlan_nic, 'up', 'promisc'])
        check_call(['virsh', 'attach-interface', self.headnode._vmname(), 'bridge', bridge, '--config'])
