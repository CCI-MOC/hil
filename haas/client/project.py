import json
from haas.client.base import ClientBase
from haas.client import errors


class Project(ClientBase):
        """ Consists of calls to query and manipulate project related
            objects and relations """

        def list(self):
            """ Lists all projects under HIL """
            url = self.object_url('/projects')
            q = self.s.get(url)
            if q.ok:
                return q.json()
            elif q.status_code == 401:
                raise errors.AuthenticationError(
                        "Make sure credentials match "
                        "chosen authentication backend."
                      )

        def nodes_in(self, project_name):
            """ Lists nodes allocated to project <project_name> """
            self.project_name = project_name
            url = self.object_url('project', self.project_name, 'nodes')
            q = self.s.get(url)
            if q.ok:
                return q.json()
            elif q.status_code == 401:
                raise errors.AuthenticationError("Invalid credentials.")
            elif q.status_code == 404:
                raise errors.NotFoundError(
                        "Project %s does not exist." % self.project_name
                        )

        def networks_in(self, project_name):
            """ Lists nodes allocated to project <project_name> """
            self.project_name = project_name
            url = self.object_url('project', self.project_name, 'networks')
            q = self.s.get(url)
            if q.ok:
                return q.json()
            elif q.status_code == 401:
                raise errors.AuthenticationError("Invalid credentials.")
            elif q.status_code == 404:
                raise errors.NotFoundError(
                        "Project %s does not exist." % self.project_name
                        )

        def create(self, project_name):
            """ Creates a project named <project_name> """
            self.project_name = project_name
            url = self.object_url('project', self.project_name)
            q = self.s.put(url)
            if q.ok:
                return
            elif q.status_code == 401:
                raise errors.AuthenticationError("Invalid credentials.")
            elif q.status_code == 409:
                raise errors.DuplicateError("Project Name not unique.")

        def delete(self, project_name):
            """ Deletes a project named <project_name> """
            self.project_name = project_name
            url = self.object_url('project', self.project_name)
            q = self.s.delete(url)
            if q.ok:
                return
            elif q.status_code == 401:
                raise errors.AuthenticationError("Invalid credentials.")
            elif q.status_code == 404:
                raise errors.NotFoundError(
                        "Deletion failed. Project does not exist."
                        )

        def connect(self, project_name, node_name):
            """ Adds a node to a project. """
            self.project_name = project_name
            self.node_name = node_name

            url = self.object_url('project', self.project_name, 'connect_node')
            payload = json.dumps({'node': self.node_name})
            q = self.s.post(url, data=payload)
            if q.ok:
                return
            elif q.status_code == 423:
                raise errors.BlockedError(
                        "Not a free node. Only free nodes can be added to a "
                        "project. "
                        )
            elif q.status_code == 404:
                raise errors.NotFoundError("Node or project does not exist.")

        def detach(self, project_name, node_name):
            """ Adds a node to a project. """
            self.project_name = project_name
            self.node_name = node_name

            url = self.object_url('project', project_name, 'detach_node')
            payload = json.dumps({'node': node_name})
            q = self.s.post(url, data=payload)
            if q.ok:
                return
            elif q.status_code == 404:
                raise errors.NotFoundError(
                        "Node or Project does not exist or "
                        "Node not owned by project"
                        )
