"""Implement the hil-admin command."""
from hil import config, model, deferred, server, migrations, rest
from hil.commands import db
from hil.commands.migrate_ipmi_info import MigrateIpmiInfo
from hil.commands.util import ensure_not_root
from hil.flaskapp import app
from time import sleep
from flask_script import Manager, Command, Option

import sys
import logging
from click import IntRange
manager = Manager(app)


class ServeNetworks(Command):
    """Start the HIL networking server"""

    # pylint: disable=arguments-differ
    def run(self):
        logger = logging.getLogger(__name__)
        server.init()
        server.register_drivers()
        server.validate_state()
        migrations.check_db_schema()

        # Check if config contains usable sleep_time
        if (config.cfg.has_section('network-daemon') and
                config.cfg.has_option('network-daemon', 'sleep_time')):
            try:
                sleep_time = config.cfg.getfloat(
                    'network-daemon', 'sleep_time')
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


class RunDevelopmentServer(Command):
    """Run a development api server. Don't use this in production.
    Specify the port with -p or --port otherwise defaults to 5000"""

    option_list = (
        Option('--port', '-p', dest='port',
               type=IntRange(0, 2**16-1), default=5000),
    )

    # pylint: disable=arguments-differ
    def run(self, port):
        if config.cfg.has_option('devel', 'debug'):
            debug = config.cfg.getboolean('devel', 'debug')
        else:
            debug = False
        # We need to import api here so that the functions within it get
        # registered (via `rest_call`), though we don't use it directly:
        # pylint: disable=unused-variable
        from hil import api
        server.init()
        migrations.check_db_schema()
        server.stop_orphan_consoles()
        rest.serve(port, debug=debug)


class CreateAdminUser(Command):
    """Create an admin user. Only valid for the database auth backend.

    This must be run on the HIL API server, with access to hil.cfg and the
    database. It will create a user named <username> with password
    <password>, who will have administrator privileges.

    This command should only be used for bootstrapping the system; once you
    have an initial admin, you can (and should) create additional users via
    the API.
    """

    # these are actually positional arguments
    option_list = (Option('username'), Option('password'))

    # pylint: disable=arguments-differ
    def run(self, username, password):
        if not config.cfg.has_option('extensions', 'hil.ext.auth.database'):
            sys.exit("'create-admin-user' is only valid with the database auth"
                     " backend.")

        from hil.ext.auth.database import User
        model.db.session.add(User(label=username, password=password,
                                  is_admin=True))
        model.db.session.commit()


manager.add_command('db', db.command)
manager.add_command('migrate-ipmi-info', MigrateIpmiInfo())
manager.add_command('serve-networks', ServeNetworks())
manager.add_command('run-dev-server', RunDevelopmentServer())
manager.add_command('create-admin-user', CreateAdminUser())


def main():
    """Entrypoint for the hil-admin command."""
    ensure_not_root()
    config.setup()
    model.init_db()
    manager.run()
