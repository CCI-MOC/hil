"""Test invoking the command line tool."""

import subprocess
import pytest
from hil.test_common import fail_on_log_warnings

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


PROJECT1 = 'foo'
PROJECT2 = 'bar'


def test_add_list_delete_projects():
    """ Test the CRUD operations on projects from the CLI.

    The project list does not need to be empty before running the test."""
    output = subprocess.check_output(['hil', 'project', 'list'])
    projects = output.split(" ")
    projects.remove('\n')
    assert PROJECT1 not in projects
    assert PROJECT2 not in projects
    size = len(projects)

    subprocess.check_call(['hil', 'project', 'create', PROJECT1])
    output = subprocess.check_output(['hil', 'project', 'list'])
    output = output.strip('\n')
    projects = output.split(" ")
    assert PROJECT1 in projects
    assert PROJECT2 not in projects
    assert len(projects) == size + 1

    subprocess.check_call(['hil', 'project', 'delete', PROJECT1])
    output = subprocess.check_output(['hil', 'project', 'list'])
    projects = output.split(" ")
    projects.remove('\n')
    assert PROJECT1 not in projects
    assert PROJECT2 not in projects
    assert len(projects) == size
