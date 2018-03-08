"""Miscellaneous commands go here"""
import click
from hil.cli.client_setup import setup_http_client

C = setup_http_client()


@click.command(name='serve', help='Run a development HIL server')
@click.argument('port', type=click.IntRange(0, 2**16-1),
                default='5000', required=False)
def serve(port):
    """Run a development api server. Don't use this in production."""
    port = int(port)
    from hil import rest, server, config, migrations
    from hil.config import cfg
    config.setup()
    if cfg.has_option('devel', 'debug'):
        debug = cfg.getboolean('devel', 'debug')
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


@click.command(name='serve_networks', help='Run the networking server')
def serve_networks():
    """Start the HIL networking server"""
    from hil import model, deferred, config, server, migrations
    from hil.config import cfg
    from time import sleep
    import logging
    import sys

    logger = logging.getLogger(__name__)
    config.setup()
    server.init()
    server.register_drivers()
    server.validate_state()
    model.init_db()
    migrations.check_db_schema()

    # Check if config contains usable sleep_time
    if (cfg.has_section('network-daemon') and
            cfg.has_option('network-daemon', 'sleep_time')):
        try:
            sleep_time = cfg.getfloat('network-daemon', 'sleep_time')
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


@click.command(name='create_admin_user', short_help='Create admin user')
@click.argument('username')
@click.argument('password')
def create_admin_user(username, password):
    """Create an admin user. Only valid for the database auth backend.

    This must be run on the HIL API server, with access to hil.cfg and the
    database. It will create an user named <username> with password
    <password>, who will have administrator privileges.

    This command should only be used for bootstrapping the system; once you
    have an initial admin, you can (and should) create additional users via
    the API.
    """
    import sys
    from hil import config

    config.setup()
    if not config.cfg.has_option('extensions', 'hil.ext.auth.database'):
        sys.exit("'make_inital_admin' is only valid with the database auth"
                 " backend.")
    from hil import model
    from hil.model import db
    from hil.ext.auth.database import User
    model.init_db()
    db.session.add(User(label=username, password=password, is_admin=True))
    db.session.commit()


@click.group(name='networking-action')
def networking_action():
    """Commands related to networking-actions"""


@networking_action.command('show')
@click.argument('status_id')
def show_networking_action(status_id):
    """Displays the status of the networking action"""
    print C.node.show_networking_action(status_id)
