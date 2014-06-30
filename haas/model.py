from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, sessionmaker,backref
from passlib.hash import sha512_crypt
from subprocess import check_call
from haas.config import cfg
from haas.dev_support import no_dry_run

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

    engine = create_engine(uri)
    if create:
        Base.metadata.create_all(engine)
    Session.configure(bind=engine)


class Model(Base):
    """All of our database models are descendants of this class.

    Its main purpose is to reduce boilerplate by doing things such as
    auto-generating table names.
    """
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    label = Column(String, unique=True)

    def __repr__(self):
        return '%s<%r>' % (self.__class__.__name__, self.label)

    @declared_attr
    def __tablename__(cls):
        """Automatically generate the table name."""
        return cls.__name__.lower()


class Nic(Model):
    mac_addr  = Column(String)

    port_id   = Column(Integer,ForeignKey('port.id'))
    node_id   = Column(Integer,ForeignKey('node.id'))

    # One to one mapping port
    port      = relationship("Port",backref=backref('nic',uselist=False))
    node      = relationship("Node",backref=backref('nics'))

    group_id = Column(Integer, ForeignKey('group.id'))
    group = relationship("Group", backref=backref("nic_list"))


    def __init__(self, label, mac_addr):
        self.label     = label
        self.mac_addr  = mac_addr


class Node(Model):
    available     = Column(Boolean)
    project_id    = Column(Integer,ForeignKey('project.id'))
    #many to one mapping to project
    project       = relationship("Project",backref=backref('nodes'))

    group_id = Column(Integer, ForeignKey('group.id'))
    group = relationship("Group", backref=backref("node_list"))

    def __init__(self, label, available = True):
        self.label   = label
        self.available = available


class Project(Model):
    deployed    = Column(Boolean)

    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    group = relationship("Group", backref=backref("project_list"))

    def __init__(self, group, label):
        self.group = group
        self.label = label
        self.deployed   = False


class Network(Model):
    project_id    = Column(String,ForeignKey('project.id'))
    project       = relationship("Project",backref=backref('networks'))

    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    group = relationship("Group", backref=backref("network_list"))

    def __init__(self, group, label):
        self.group = group
        self.label = label


class Vlan(Model):
    """A VLAN

    This is used to track which vlan numbers are available; when a Network is
    created, it must allocate a Vlan, to ensure that:

    1. The VLAN number it is using is unique, and
    2. The VLAN number is actually allocated to the HaaS; on some deployments we
       may have specific vlan numbers that we are allowed to use.
    """
    vlan_no = Column(Integer, nullable=False)

    network_id = Column(Integer,ForeignKey('network.id'))
    network = relationship('Network', backref=backref('vlan'))

    def __init__(self, vlan_no):
        self.vlan_no = vlan_no


class Port(Model):
    port_no       = Column(Integer)
    switch_id     = Column(Integer,ForeignKey('switch.id'))
    switch        = relationship("Switch",backref=backref('ports'))

    group_id = Column(Integer, ForeignKey('group.id'))
    group = relationship("Group", backref=backref("port_list"))

    def __init__(self, label, port_no):
        self.label   = label
        self.port_no   = port_no


class Switch(Model):
    model         = Column(String)

    def __init__(self,label,model):
        self.label = label
        self.model = model


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

    project_id    = Column(String, ForeignKey('project.id'))
    project       = relationship("Project", backref = backref('headnode',uselist = False))

    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    group = relationship("Group", backref=backref("hn_list"))

    def __init__(self, group, label, available = True):
        self.group = group
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
    headnode_id    = Column(String, ForeignKey('headnode.id'), nullable=False)
    headnode       = relationship("Headnode", backref = backref('hnics'))

    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    group = relationship("Group", backref=backref("hnic_list"))

    def __init__(self, group, headnode, label, mac_addr):
        self.headnode = headnode
        self.group = group
        self.label = label
        self.mac_addr = mac_addr
