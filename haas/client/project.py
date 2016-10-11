from haas.client.base import *
from haas.client.client_errors import *


class Project(ClientBase):
        """ Consists of calls to query and manipulate project related
            objects and relations """

        def list(self):
            """ Lists all projects under HIL """
            url = self.object_url('/projects')
            q = requests.get(url, headers={"Authorization": "Basic %s" % self.auth})
            if q.ok:
                return q.json()
            elif q.status_code == 401:
                raise AuthenticationError("Make sure credentials match chosen authentication backend.")

        def nodes_in(self, project_name):
            """ Lists nodes allocated to project <project_name> """
            self.project_name = project_name
            url = self.object_url('project', self.project_name, 'nodes')
            q = requests.get(url, headers={"Authorization": "Basic %s" % self.auth})
            if q.ok:
                return q.json()
            elif q.status_code == 401:
                raise AuthenticationError("Invalid credentials.")
            elif q.status_code == 404:
                raise NotFoundError("Project %s does not exist." % self.project_name)


        def networks_in(self, project_name):
            """ Lists nodes allocated to project <project_name> """
            self.project_name = project_name
            url = self.object_url('project', self.project_name, 'networks')
            q = requests.get(url, headers={"Authorization": "Basic %s" % self.auth})
            if q.ok:
                return q.json()
            elif q.status_code == 401:
                raise AuthenticationError("Invalid credentials.")
            elif q.status_code == 404:
                raise NotFoundError("Project %s does not exist." % self.project_name)

        def create(self, project_name):
            """ Creates a project named <project_name> """
            self.project_name = project_name
            url = self.object_url('project', self.project_name)
            q = requests.put(url, headers={"Authorization": "Basic %s" % self.auth})
            if q.ok:
                return
            elif q.status_code == 401:
                raise AuthenticationError("Invalid credentials.")
            elif q.status_code == 409:
                raise DuplicateError("Project Name not unique.")

        def delete(self, project_name):
            """ Deletes a project named <project_name> """
            self.project_name = project_name
            url = self.object_url('project', self.project_name)
            q = requests.delete(url, headers={"Authorization": "Basic %s" % self.auth})
            if q.ok:
                return
            elif q.status_code == 401:
                raise AuthenticationError("Invalid credentials.")
            elif q.status_code == 404:
                raise NotFoundError("Deletion failed. Project does not exist.")

#        def add_node(self, project_name, node_name):
#            """ Adds a node to a project. """
#            self.project_name = project_name
#            self.node_name = node_name
#
#            url = self.object_url('project', project_name, 'connect_node')





