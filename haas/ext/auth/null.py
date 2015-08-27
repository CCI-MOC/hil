from haas import auth


class NullAuthBackend(auth.AuthBackend):

    def authenticate(self):
        pass

    def have_admin(self):
        return True

    def have_project_access(self, project):
        return True


def setup(*args, **kwargs):
    auth.set_auth_backend(NullAuthBackend())
