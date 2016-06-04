import ast
import pytest
import subprocess

PROJECT1 = 'foo'


class TestCLI:
    def test_add_list_delete_projects(self):
        output = subprocess.check_output(['haas', 'list_projects'])
        projects = ast.literal_eval(output)
        size = len(projects)

        subprocess.check_call(['haas', 'project_create', PROJECT1])
        output = subprocess.check_output(['haas', 'list_projects'])
        projects = ast.literal_eval(output)
        assert PROJECT1 in projects
        assert len(projects) == size + 1

        subprocess.check_call(['haas', 'project_delete', PROJECT1])
        output = subprocess.check_output(['haas', 'list_projects'])
        projects = ast.literal_eval(output)
        assert PROJECT1 not in projects
        assert len(projects) == size
