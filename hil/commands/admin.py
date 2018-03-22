"""Implement the hil-admin command."""
from hil import config, model
from hil.commands import db
from hil.commands.migrate_ipmi_info import MigrateIpmiInfo
from hil.commands.util import ensure_not_root
from hil.flaskapp import app
from flask_script import Manager

manager = Manager(app)
manager.add_command('db', db.command)
manager.add_command('migrate-ipmi-info', MigrateIpmiInfo())


def main():
    """Entrypoint for the hil-admin command."""
    ensure_not_root()
    config.setup()
    model.init_db()
    manager.run()
