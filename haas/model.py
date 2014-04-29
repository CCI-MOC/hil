from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker,backref

Base=declarative_base()

class Nic(Base):
    __tablename__ = 'nics'
    meta      = ["id", "label", "mac_addr", "node_label", "port_label"]
    id        = Column(Integer, primary_key = True)
    label     = Column(String)
    mac_addr  = Column(String)

    port_label   = Column(Integer,ForeignKey('ports.label'))
    node_label   = Column(Integer,ForeignKey('nodes.label'))
    
    # One to one mapping port
    port      = relationship("Port",backref=backref('nic',uselist=False))
    node      = relationship("Node",backref=backref('nics',order_by=label)) 
    
    def __init__(self,label, mac_addr):
        self.label     = label
        self.mac_addr  = mac_addr
            
class Node(Base):
    __tablename__='nodes'

    meta          = ["id","label","available","project"]
    id            = Column(Integer,primary_key=True)
    label         = Column(String)
    available     = Column(Boolean)
    project_label = Column(String,ForeignKey('groups.group_name'))
    
    
    #many to one mapping to project
    project       = relationship("Project",backref=backref('nodes',order_by=id))

    

    def __init__(self, label, available = True):
        self.label   = label
        self.available = available

    
class Project(Base):
    __tablename__='projects'
    meta        = ["id", "label", "deployed", "group_label"]
    id          = Column(Integer, primary_key = True)
    label       = Column(String, primary_key = True)
    deployed    = Column(Boolean)
    group_label = Column(String,ForeignKey('groups.label'))


    #Many to one mapping to User
    group       = relationship("Group",backref=backref('groups',order_by=label))

    def __init__(self, label):
        self.label = label
        self.deployed   = False


class Vlan(Base):
    __tablename__ ='vlans'
    meta          = ["id", "label", "available", "nic_label", "project_label"]
    id            = Column(Integer,primary_key=True)
    label         = Column(String)
    available     = Column(Boolean)

    project_label = Column(String,ForeignKey('projects.label'))
    
    project         = relationship("Project",backref=backref('vlans',order_by=nic_label))
    def __init__(self,label, nic_label, available=True):
        self.label = label
        self.nic_label = label
        self.available = available


class Port(Base):
    __tablename__ = 'ports'
    meta          = ["id","label", "switch_label","port#"]
    id            = Column(Integer,primary_key=True)
    port_no       = Column(Integer)
    switch_label  = Column(Integer,ForeignKey('switches.label'))

    switch        = relationship("Switch",backref=backref('ports',order_by=label))

    def __init__(self,label, port_no):
        self.label   = label
        self.port_no   = port_no
        

class Switch(Base):
    __tablename__ = 'switches'
    meta          = ["id","label", "model"]
    id            = Column(Integer,primary_key=True)
    label         = Column(String)
    model         = Column(String)

    def __init__(self,label,model):
        self.label = label
        self.model = model
 
class User(Base):
    __tablename__ = 'users'
    meta        = ["id", "label", "hashed_password"]
    id          = Column(Integer, primary_key = True)
    label       = Column(String)  #username
    hashed_password    = Column(String)
    
    def __init__(self, label, password):
        self.label = label
        self.set_password(password)
    
    def verify_password(self, password):
        return sha512_crypt.verify(password, self.hashed_password)
    
    def set_password(self, password):
        self.hashed_password = sha512_crypt.encrypt(password)
    
        
engine=create_engine('sqlite:///haas.db',echo=False)
Base.metadata.create_all(engine)
Session=sessionmaker(bind=engine)
session=Session()
