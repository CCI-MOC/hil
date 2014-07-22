from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, sessionmaker,backref
from passlib.hash import sha512_crypt
from subprocess import check_call
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

    driver.init_db()


class Model(Base):
    """All of our database models are descendants of this class.

    Its main purpose is to reduce boilerplate by doing things such as
    auto-generating table names.
    """
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    label = Column(String)

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
    deployed    = Column(Boolean)

    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    group = relationship("Group", backref=backref("projects"))

    def __init__(self, group, label):
        self.group = group
        self.label = label
        self.deployed   = False


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
    available     = Column(Boolean)

    project_id    = Column(String, ForeignKey('project.id'), nullable=False)
    project       = relationship("Project", backref = backref('headnode',uselist = False))

    def __init__(self, project, label, available = True):
        self.project = project
        self.label  = label
        self.available = available

    @no_dry_run
    def create(self):
        """Creates the vm within libvirt, by cloning the base image.

        The vm is not started at this time.
        """
        check_call(['virt-clone', '-o', 'base-headnode', '-n', self._vmname(), '--auto-clone'])

    @no_dry_run
    def start(self):
        """Powers on the vm, which must have been previously created."""
        check_call(['virsh', 'start', self._vmname()])

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
        vlan_no = str(self.network.vlan_no)
        bridge = 'br-vlan%s' % vlan_no
        vlan_nic = '%s.%s' % (trunk_nic, vlan_no)
        check_call(['brctl', 'addbr', bridge])
        check_call(['vconfig', 'add', trunk_nic, vlan_no])
        check_call(['brctl', 'addif', bridge, vlan_nic])
        check_call(['ifconfig', bridge, 'up', 'promisc'])
        check_call(['ifconfig', vlan_nic, 'up', 'promisc'])
        check_call(['virsh', 'attach-interface', self.headnode._vmname(), 'bridge', bridge, '--config'])
