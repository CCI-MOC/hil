"""Miscellaneous commands go here"""
import click
from hil.cli.client_setup import setup_http_client

C = setup_http_client()


@click.command(name='serve', help='Run a development HIL server')
@click.argument('port', type=click.IntRange(0,2**16-1),
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
    from hil import model, deferred, config
    from time import sleep
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