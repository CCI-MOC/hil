import json
from haas.client.base import ClientBase
from haas.client import errors


class User(ClientBase):
    """ Consists of calls to query and manipulate users related
    objects and relations.
    """

    def create(self, username, password, privilege):
        """Create a user <username> with password <password>.
    <privilege> may by either "admin" or "regular", and determines whether a
    user is authorized for administrative privileges
    """
        self.username = username
        self.password = password
        self.privilege = privilege
        url = self.object_url('/auth/basic/user', self.username)

        if privilege not in('admin', 'regular'):
            raise TypeError(
                "invalid privilege type: must be either  'admin' or 'regular'."
                )
        payload = json.dumps({
                'password': self.password, 'is_admin': privilege == 'admin',
                })
        q = self.s.put(url, data=payload)
        if q.ok:
            return
        elif q.status_code == 401:
            raise errors.AuthenticationError( 
                    "You do not have rights for user creation "
                    )
        elif q.status_code == 409:
            raise errors.DuplicateError( "User already exists. ")

    def delete(self, username):
        """Deletes the user <username>. """
        self.username = username
        url = self.object_url('/auth/basic/user', self.username)
        q = self.s.delete(url)
        if q.ok:
            return
        elif q.status_code == 404:
            raise errors.NotFoundError(
                    "User deletion failed. No such user. "
                    )


    def grant_access(self, user, project):
        """Grants permission to <user> to access resources of <project>. """
     #Note: Named such so that in future we can have granular access to projects
     #like "grant_read_access", "grant_write_access", "grant_all_access", etc
        self.user = user
        self.project = project
        url = self.object_url('/auth/basic/user', self.user, 'add_project')
        payload = json.dumps({ 'project': self.project })
        q = self.s.post(url, data=payload)
        if q.ok:
            return
        elif q.status_code == 404:
            raise errors.NotFoundError(
                    "Operation failed. Either user or project does not exist. "
                    )
        elif q.status_code == 409:
            raise errors.DuplicateError(
                    "Access already granted. Duplicate operation. "
                    )



    def remove_access(self, user, project):
        """ Removes all access of <user> to <project>. """
        self.user = user
        self.project = project
        url = self.object_url('/auth/basic/user', self.user, 'remove_project')
        payload = json.dumps({ 'project': self.project })
        q = self.s.post(url, data=payload)
        if q.ok:
            return
        elif q.status_code == 404:
            raise errors.NotFoundError(
                    "Operation failed. Either user; project or their "
                    "relationship does not exist. "
                    )






