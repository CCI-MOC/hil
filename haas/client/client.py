from haas.client.base import ClientBase
from haas.client.node import Node
from haas.client.project import Project
from haas.client.switch import Switch
from haas.client.network import Network
from haas.client import auth


class Client(object):

    def __init__(self, endpoint, sess):
        self.endpoint = endpoint
        self.s = sess
        self.node = Node(self.endpoint, self.s)
        self.project = Project(self.endpoint, self.s)
        self.switch = Switch(self.endpoint, self.s)
        self.network = Network(self.endpoint, self.s)
