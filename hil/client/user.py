"""Client library for user-oriented api calls.

These are only meaningful if the server is configured to use
username & password auth.
"""
import json
from hil.client.base import ClientBase


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
        return self.check_response(
                self.httpClient.request("PUT", url, data=payload)
                )

    def delete(self, username):
        """Deletes the user <username>. """
        url = self.object_url('/auth/basic/user', username)
        return self.check_response(
                self.httpClient.request("DELETE", url)
                )

    def add(self, user, project):
        """Adds <user> to a <project>. """
        url = self.object_url('/auth/basic/user', user, 'add_project')
        payload = json.dumps({'project': project})
        return self.check_response(
                self.httpClient.request("POST", url, data=payload)
                )

    def remove(self, user, project):
        """Removes all access of <user> to <project>. """
        url = self.object_url('/auth/basic/user', user, 'remove_project')
        payload = json.dumps({'project': project})
        return self.check_response(
                self.httpClient.request("POST", url, data=payload)
                )

    def set_admin(self, username, is_admin):
        """Changes the admin status of <username>.

        <is_admin> is a boolean that determines
        whether a user is authorized for
        administrative privileges.
        """

        url = self.object_url('/auth/basic/user', username)
        payload = json.dumps({'is_admin': is_admin})
        return self.check_response(
                self.httpClient.request("PATCH", url, data=payload)
                )
