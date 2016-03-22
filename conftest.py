"""pytest hooks"""
from os.path import dirname, join, realpath


def pytest_ignore_collect(path, config):
    # env.py must only be imported in particular environments provided by
    # alembic. This hook prevents pytest from importing env.py during its
    # collection phase.
    env_path = join(dirname(__file__), 'haas', 'migrations', 'env.py')
    return realpath(str(path)) == realpath(env_path)
