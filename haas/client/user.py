import json
from haas.client.base import ClientBase
from haas.client import errors


class User(ClientBase):
    """Consists of calls to query and

    manipulate users related objects and relations.
    """

    def create(self, username, password, privilege):
        """Create a user <username> with password <password>.

        <privilege> may by either "admin" or "regular",
        and determines whether a user is authorized for
        administrative privileges.
        """
        url = self.object_url('/auth/basic/user', username)

        if privilege not in('admin', 'regular'):
            raise ValueError(
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

    def add(self, user, project):
        """Adds <user> to a <project>. """
        url = self.object_url('/auth/basic/user', user, 'add_project')
        payload = json.dumps({'project': project})
        return self.check_response(self.s.post(url, data=payload))

    def remove(self, user, project):
        """Removes all access of <user> to <project>. """
        url = self.object_url('/auth/basic/user', user, 'remove_project')
        payload = json.dumps({'project': project})
        return self.check_response(self.s.post(url, data=payload))
