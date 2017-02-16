import json
from haas.client.base import ClientBase
from haas.client import errors


class Project(ClientBase):
        """ Consists of calls to query and manipulate project related
            objects and relations """

        def list(self):
            """ Lists all projects under HIL """

            self.url = self.object_url('/projects')
            return self.check_response(self.s.get(self.url))

        def nodes_in(self, project_name):
            """ Lists nodes allocated to project <project_name> """
            self.project_name = project_name
            self.url = self.object_url('project', self.project_name, 'nodes')
            return self.check_response(self.s.get(self.url))

        def networks_in(self, project_name):
            """ Lists nodes allocated to project <project_name> """
            self.project_name = project_name
            self.url = self.object_url(
                    'project', self.project_name, 'networks'
                    )
            return self.check_response(self.s.get(self.url))

        def create(self, project_name):
            """ Creates a project named <project_name> """
            self.project_name = project_name
            self.url = self.object_url('project', self.project_name)
            return self.check_response(self.s.put(self.url))

        def delete(self, project_name):
            """ Deletes a project named <project_name> """
            self.project_name = project_name
            self.url = self.object_url('project', self.project_name)
            return self.check_response(self.s.delete(self.url))

        def connect(self, project_name, node_name):
            """ Adds a node to a project. """
            self.project_name = project_name
            self.node_name = node_name

            self.url = self.object_url(
                    'project', self.project_name, 'connect_node'
                    )
            self.payload = json.dumps({'node': self.node_name})
            return self.check_response(
                    self.s.post(self.url, data=self.payload)
                    )

        def detach(self, project_name, node_name):
            """ Adds a node to a project. """
            self.project_name = project_name
            self.node_name = node_name

            self.url = self.object_url('project', project_name, 'detach_node')
            self.payload = json.dumps({'node': node_name})
            return self.check_response(
                    self.s.post(self.url, data=self.payload)
                    )
