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

        def _for_project(self, project_name):
            """ Lists all nodes allocated to a given <project> """

            self.project_name = project_name
            project_root = "/project/"+self.project_name
            return project_root

        def nodes_in(self, project_name):
            """ Lists nodes allocated to project <project_name> """
            self.project_name = project_name
            base_url = self. _for_project(self.project_name)
            node_list = base_url+"/nodes"
            url = self.object_url(node_list)
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
            base_url = self. _for_project(self.project_name)
            node_list = base_url+"/networks"
            url = self.object_url(node_list)
            q = requests.get(url, headers={"Authorization": "Basic %s" % self.auth})
            if q.ok:
                return q.json()
            elif q.status_code == 401:
                raise AuthenticationError("Invalid credentials.")
            elif q.status_code == 404:
                raise NotFoundError("Project %s does not exist." % self.project_name)


            

