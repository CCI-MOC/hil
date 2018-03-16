"""Implement the hil-admin command."""
from hil import config, model, deferred, server, migrations, rest
from hil.commands import db
from hil.commands.migrate_ipmi_info import MigrateIpmiInfo
from hil.commands.util import ensure_not_root
from hil.flaskapp import app


from time import sleep
from flask_script import Manager


import sys
import logging
from click import IntRange

manager = Manager(app)

manager.add_command('db', db.command)
manager.add_command('migrate-ipmi-info', MigrateIpmiInfo())


@manager.command
def serve_networks():
    """Start the HIL networking server"""
    logger = logging.getLogger(__name__)
    server.init()
    server.register_drivers()
    server.validate_state()
    migrations.check_db_schema()

    # Check if config contains usable sleep_time
    if (config.cfg.has_section('network-daemon') and
            config.cfg.has_option('network-daemon', 'sleep_time')):
        try:
            sleep_time = config.cfg.getfloat('network-daemon', 'sleep_time')
        except (ValueError):
            sys.exit("Error: sleep_time set to non-float value")
        if sleep_time <= 0 or sleep_time >= 3600:
            sys.exit("Error: sleep_time not within bounds "
                     "0 < sleep_time < 3600")
        if sleep_time > 60:
            logger.warn('sleep_time greater than 1 minute.')
    else:
        sleep_time = 2

    while True:
        # Empty the journal until it's empty; then delay so we don't tight
        # loop.
        while deferred.apply_networking():
            pass
        sleep(sleep_time)


@manager.option('-p', '--port', type=IntRange(0, 2**16-1), default=5000)
def run_dev_server(port):
    """Run a development api server. Don't use this in production.
    Specify the port with -p or --port otherwise defaults to 5000"""
    if config.cfg.has_option('devel', 'debug'):
        debug = config.cfg.getboolean('devel', 'debug')
    else:
        debug = False
    # We need to import api here so that the functions within it get registered
    # (via `rest_call`), though we don't use it directly:
    # pylint: disable=unused-variable
    from hil import api
    server.init()
    migrations.check_db_schema()
    server.stop_orphan_consoles()
    rest.serve(port, debug=debug)


@manager.command
def create_admin_user(username, password):
    """Create an admin user. Only valid for the database auth backend.


    This must be run on the HIL API server, with access to hil.cfg and the
    database. It will create a user named <username> with password
    <password>, who will have administrator privileges.

    This command should only be used for bootstrapping the system; once you
    have an initial admin, you can (and should) create additional users via
    the API.
    """
    if not config.cfg.has_option('extensions', 'hil.ext.auth.database'):
        sys.exit("'make_inital_admin' is only valid with the database auth"
                 " backend.")

    from hil.ext.auth.database import User
    model.db.session.add(User(label=username, password=password,
                              is_admin=True))
    model.db.session.commit()


def main():
    """Entrypoint for the hil-admin command."""
    ensure_not_root()
    config.setup()
    model.init_db()
    manager.run()
