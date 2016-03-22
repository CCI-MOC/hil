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
branch_labels = ('haas',)

from alembic import op


def upgrade():
    op.rename_table('networkattachment', 'network_attachment')
    op.rename_table('networkingaction', 'networking_action')


def downgrade():
    op.rename_table('network_attachment', 'networkattachment')
    op.rename_table('networking_action', 'networkingaction')
