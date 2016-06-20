from haas.client.base import ClientBase
from haas.client.node import Node
from haas.client.project import Project
from haas.client.switch import Switch
from haas.client.auth import auth_db



class Client(object):

    def __init__(self, endpoint, auth):
        self.endpoint = endpoint
        self.auth = auth
        self.node = Node(self.endpoint, self.auth)
        self.project = Project(self.endpoint, self.auth)
        self.switch = Switch(self.endpoint, self.auth)

