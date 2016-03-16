"""Rename tables to account for Flask-SQLAlchemy's auto-naming.

Unlike our own (old) table name generator, Flask-SQLAlchemy inserts
underscores in names that are CamelCase (i.e. table names are snake_case).
There's no reason to keep the old behavior, but we need this migration script
otherwise.

Revision ID: 6a8c19565060
Revises: None
Create Date: 2016-03-15 23:40:11.411599
"""

# revision identifiers, used by Alembic.
revision = '6a8c19565060'
down_revision = None

from alembic import op
import sys


def upgrade():
    if 'haas.ext.switches.dell' in sys.modules:
        op.rename_table('powerconnect55xx', 'power_connect55xx')
    if 'haas.ext.switches.mock' in sys.modules:
        op.rename_table('mockswitch', 'mock_switch')
    op.rename_table('networkattachment', 'network_attachment')
    op.rename_table('networkingaction', 'networking_action')


def downgrade():
    if 'haas.ext.switches.dell' in sys.modules:
        op.rename_table('power_connect55xx', 'powerconnect55xx')
    if 'haas.ext.switches.mock' in sys.modules:
        op.rename_table('mock_switch', 'mockswitch')
    op.rename_table('network_attachment', 'networkattachment')
    op.rename_table('networking_action', 'networkingaction')
