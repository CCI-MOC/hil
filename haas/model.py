from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, sessionmaker,backref
from passlib.hash import sha512_crypt
from haas.config import cfg

Base=declarative_base()
Session = sessionmaker()

user_groups = Table('user_groups', Base.metadata,
                    Column('user_id', Integer, ForeignKey('user.id')),
                    Column('group_id', Integer, ForeignKey('group.id')))


def init_db(create=False):
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

    @declared_attr
    def __tablename__(cls):
        """Automatically generate the table name."""
        return cls.__name__.lower()


class Nic(Model):
    __tablename__ = 'nics'
    # The "meta" attribute is for the benefit of the cli, which uses it to
    # display column names. There's probably a better way to do this, but the
    # intent going forward is for the cli to be talking to the rest api, rather
    # than this module, so let's not bother for now, and just remember to remove
    # this (as well as the same attribute in other classes) when we can.
    meta      = ["id", "label", "mac_addr", "node_label", "port_label"]
    id        = Column(Integer, primary_key = True)
    label     = Column(String)
    mac_addr  = Column(String)

    port_label   = Column(Integer,ForeignKey('port.label'))
    node_label   = Column(Integer,ForeignKey('node.label'))
    
    # One to one mapping port
    port      = relationship("Port",backref=backref('nic',uselist=False))
    node      = relationship("Node",backref=backref('nics',order_by=label)) 
    
    def __init__(self,label, mac_addr):
        self.label     = label
        self.mac_addr  = mac_addr
    def __repr__(self):
        return 'Nic<%r %r %r %r %r>'%(self.id,
                                      self.label,
                                      self.mac_addr,
                                      self.port_label if self.port else None,
                                      self.node_label if self.node else None)
            
class Node(Model):

    meta          = ["id","label","available","project"]
    id            = Column(Integer,primary_key=True)
    label         = Column(String)
    available     = Column(Boolean)
    project_label = Column(String,ForeignKey('project.label'))
        
    #many to one mapping to project
    project       = relationship("Project",backref=backref('nodes',order_by=id))

    def __init__(self, label, available = True):
        self.label   = label
        self.available = available

    def __repr__(self):
        return "Node<%r %r %r %r>"%(self.id, 
                                    self.label,
                                    self.available,
                                    self.project_label if self.project else None)
    
class Project(Model):
    meta        = ["id", "label", "deployed", "group_label"]
    id          = Column(Integer, primary_key = True)
    label       = Column(String)
    deployed    = Column(Boolean)
    group_label = Column(String,ForeignKey('group.label'))


    #Many to one mapping to User
    group       = relationship("Group",backref=backref('group',order_by=label))

    def __init__(self, label):
        self.label = label
        self.deployed   = False
    def __repr__(self):
        return "Project<%r %r %r %r>"%(self.id,
                                       self.label,
                                       self.deployed,
                                       self.group_label if self.group else None)

class Vlan(Model):
    meta          = ["id", "label", "available", "nic_label", "project_label"]
    id            = Column(Integer,primary_key=True)
    label         = Column(String)
    available     = Column(Boolean)
    nic_label     = Column(String)
    project_label = Column(String,ForeignKey('project.label'))
    
    project         = relationship("Project",backref=backref('vlans',order_by=nic_label))
    def __init__(self,label, nic_label, available=True):
        self.label = label
        self.nic_label = nic.label
        self.available = available
    def __repr__(self):
        return 'Vlan<%r %r %r %r %r>'%(self.id,
                                       self.label,
                                       self.available,
                                       self.nic_label,
                                       self.project_label if self.project else None)

class Port(Model):
    meta          = ["id","label", "switch_label","port#"]
    id            = Column(Integer,primary_key=True)
    label         = Column(String)
    port_no       = Column(Integer)
    switch_label  = Column(Integer,ForeignKey('switch.label'))

    switch        = relationship("Switch",backref=backref('ports',order_by=label))

    def __init__(self,label, port_no):
        self.label   = label
        self.port_no   = port_no
    def __repr__(self):
        return 'Port<%r %r %r %r>'%(self,id,
                                    self.label,
                                    self.port_no,
                                    self.switch_label if self.switch else None)

class Switch(Model):
    meta          = ["id","label", "model"]
    id            = Column(Integer,primary_key=True)
    label         = Column(String)
    model         = Column(String)

    def __init__(self,label,model):
        self.label = label
        self.model = model
    def __repr__(self):
        return 'Switch<%r %r %r>'%(self.id,
                                   self.label,
                                   self.model)

class User(Model):
    meta        = ["id", "label", "hashed_password"]
    id          = Column(Integer, primary_key = True)
    label       = Column(String)  #username
    hashed_password    = Column(String)
    
    #many to many User<->Group
    """
    alice = User('alice', 'alice')
    g1    = Group('g1')
    alice.groups.append(g1)
    """
    groups      = relationship('Group', secondary = user_groups, backref = 'user' )
    def __init__(self, label, password):
        self.label = label
        self.set_password(password)
    
    def verify_password(self, password):
        return sha512_crypt.verify(password, self.hashed_password)
    
    def set_password(self, password):
        self.hashed_password = sha512_crypt.encrypt(password)
    
    def __repr__(self):
        return "User<%r %r %r %r>"%(self.id,
                                    self.label,
                                    self.hashed_password,
                                    self.groups)
    
class Group(Model):
    meta          = ["id", "label"]
    id            = Column(Integer, primary_key = True)
    label         = Column(String)
    
    def __init__(self, label):
        self.label = label
    
    def __repr__(self):
        return 'Group<%r %r>'%(self.id,
                               self.label)

class Headnode(Model):
    meta          = ["id","label","available", "project_label"]
    id            = Column(Integer, primary_key = True)
    label         = Column(String)
    available     = Column(Boolean)
    
    project_label = Column(String, ForeignKey('project.label'))
    project       = relationship("Project", backref = backref('headnode',uselist = False))

    def __init__(self, label, available = True):
        self.label  = label
        self.available = available

    def __repr__(self):
        return 'Headnode<%r %r %r>'%(self.id,
                                     self.available,
                                     self.label,
                                     self.project_label if self.project else None)
class Hnic(Model):
    meta           = ["id", "label","mac_addr","headnode_label" ]
    id             = Column(Integer, primary_key = True)
    label          = Column(String)
    mac_addr       = Column(String)
    headnode_label = Column(String, ForeignKey('headnode.label'))

    headnode       = relationship("Headnode", backref = backref('hnics',order_by=label))

    def __init__(self, label, mac_addr):
        self.label = label
        self.mac_addr = mac_addr

    def __repr__(self):
        return "Hnic<%r %r %r %r>"%(self.id,
                                    self.label,
                                    self.mac_addr,
                                    self.headnode_label if self.headnode else None)
"""
alice = User('alice','alice')
bob   = User('bob','bob')
admin = Group('admin')
student = Group('student')
alice.groups.append(admin)
alice.groups.append(student)
session.add(alice)
print session.query(User).all()
"""
