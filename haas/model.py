from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import *
from passlib.hash import sha512_crypt

from haas.config import cfg

Base = declarative_base()
Session = sessionmaker()

def init_db(create=False):
    uri = cfg.get('database', 'uri')
    engine = create_engine(uri)
    if create:
        Base.metadata.create_all(engine)
    Session.configure(bind=engine)

class Model(Base):
    """All of our database models are descendants of this class.

    It provides some base functionality that we want everywhere.
    """
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        """Automatically generate the table name."""
        return cls.__name__.lower()

    label = Column(String, primary_key=True)


# Various joining tables, for many-to-many relationships:
_m2m = {}
_m2m_pairs = [ ('group', 'user') ]
for left, right in _m2m_pairs:
    _m2m[(left, right)] = Table(left + '_to_' + right, Base.metadata,
            Column(left + '_label', String, ForeignKey(left + '.label')),
            Column(right + '_label', String, ForeignKey(right + '.label')),
            )


class Group(Model):
    users = relationship('User', secondary=_m2m[('group', 'user')], backref='groups')

class Headnode(Model): pass
class Hnic(Model): pass
class Network(Model): pass
class Nic(Model): pass
class Node(Model):
    """A node is a physical computer
    The node id is the object's label
    """
    available  = Column(Boolean)
    project_name = Column(String,ForeignKey('Project.label'))
    #Many to one mapping to group
    project    = relationship("Project",backref=backref('nodes',order_by=label))
    def __init__(self,node_id):
        self.label = node_id
    
class Port(Model): pass
class Project(Model): pass
class Switch(Model): pass

class User(Model):
    """A HaaS user account.
   
    The username is the object's label.
    """
    hashed_password = Column(String) # hashed and salted with passlib (sha512)

    def __init__(self, name, password):
        self.label = name
        self.set_password(password)

    def verify_password(self, password):
        """verifies that `password` is the correct password for the user.

        `password` should be the plaintext password. It will be checked
        against the salted/hashed one in the database.
        """
        return sha512_crypt.verify(password, self.hashed_password)

    def set_password(self, password):
        """Sets the user's password to `password`.

        `password` should be the plaintext of the password, not the hash.
        """
        self.hashed_password = sha512_crypt.encrypt(password)
