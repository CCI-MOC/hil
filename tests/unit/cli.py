"""Tests for the command line tools.

Note that this is not just `hil.cli`, but `hil.command` as well.
"""
import pytest
import tempfile
import os
import signal
from subprocess import check_call, check_output, Popen, CalledProcessError, \
    STDOUT
from time import sleep
from hil.test_common import fail_on_log_warnings


fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


@pytest.fixture(autouse=True)
def make_config(request):
    """Generate a temporary config file."""
    tmpdir = tempfile.mkdtemp()
    cwd = os.getcwd()
    os.chdir(tmpdir)
    with open('hil.cfg', 'w') as f:
        # We need to make sure the database ends up in the tmpdir directory,
        # and Flask-SQLAlchemy doesn't seem to want to do relative paths, so
        # we can't just do a big string literal.
        config = '\n'.join([
            '[headnode]',
            'base_imgs = base-headnode, img1, img2, img3, img4',
            '[database]',
            'uri = sqlite:///%s/hil.db' % tmpdir,
            '[extensions]',
            'hil.ext.auth.null =',
            'hil.ext.network_allocators.null =',
        ])
        f.write(config)

    def cleanup():
        """Remove the config file, database, and temp dir."""
        os.remove('hil.cfg')
        os.remove('hil.db')
        os.chdir(cwd)
        os.rmdir(tmpdir)

    request.addfinalizer(cleanup)


def test_db_create():
    """Create the database via the cli."""
    check_call(['hil-admin', 'db', 'create'])


def runs_for_seconds(cmd, seconds=1):
    """Test if the command ``cmd`` runs for at least ``seconds`` seconds.

    ``cmd`` is a list containing the name of a command and its arguments.

    ``seconds`` is a number of seconds (by default 1).

    ``run_for_seconds`` will execute ``cmd``, wait for ``seconds`` seconds,
    send SIGTERM to the process, and then wait() for it. If the exit status
    indicates that it stopped for any reason other than SIGTERM,
    ``run_for_seconds`` returns False, otherwise it returns True.

    This is useful to check that a server process does not immediately die on
    startup, though it's a bit of a hack --- checking rigorously would require
    extra knowledge of the workings of that process (hooray for the halting
    problem).
    """
    proc = Popen(cmd)
    sleep(seconds)
    proc.terminate()
    status = proc.wait()
    return status == -signal.SIGTERM


def test_serve():
    """Check that hil serve doesn't immediately die."""
    check_call(['hil-admin', 'db', 'create'])
    assert runs_for_seconds(['hil', 'serve', '5000'], seconds=1)


def test_serve_networks():
    """Check that hil serve_networks doesn't immediately die."""
    check_call(['hil-admin', 'db', 'create'])
    assert runs_for_seconds(['hil', 'serve_networks'], seconds=1)


@pytest.mark.parametrize('command', [
    ['hil', 'serve', '5000'],
    ['hil', 'serve_networks'],
])
def test_db_init_error(command):
    """Test that a command fails if the database has not been created."""
    try:
        check_output(command, stderr=STDOUT)
        assert False, 'Should have failed, but exited successfully.'
    except CalledProcessError as e:
        assert 'Database schema is not initialized' in e.output, (
            'Should have printed an error re: database initialization, '
            'but printed %r' % e.output
        )
