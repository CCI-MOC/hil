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
        url = self.object_url('/auth/basic/user', username)

        if privilege not in('admin', 'regular'):
            raise TypeError(
                "invalid privilege type: must be either  'admin' or 'regular'."
                )
        payload = json.dumps({
                'password': password, 'is_admin': privilege == 'admin',
                })
        return self.check_response(self.s.put(url, data=payload))

    def delete(self, username):
        """Deletes the user <username>. """
        url = self.object_url('/auth/basic/user', username)
        return self.check_response(self.s.delete(url))

    def grant_access(self, user, project):
        """Grants permission to <user> to access resources of <project>. """
        # Note: Named such so that in future we can have granular
        # access to projects
        # like "grant_read_access", "grant_write_access",
        # "grant_all_access", etc
        url = self.object_url('/auth/basic/user', user, 'add_project')
        payload = json.dumps({'project': project})
        return self.check_response(self.s.post(url, data=payload))

    def revoke_access(self, user, project):
        """ Removes all access of <user> to <project>. """
        url = self.object_url('/auth/basic/user', user, 'remove_project')
        payload = json.dumps({'project': project})
        return self.check_response(self.s.post(url, data=payload))
