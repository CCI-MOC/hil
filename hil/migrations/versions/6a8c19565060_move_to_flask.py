"""Rename tables to account for Flask-SQLAlchemy's auto-naming.

Unlike our own (old) table name generator, Flask-SQLAlchemy inserts
underscores in names that are CamelCase (i.e. table names are snake_case).
There's no reason to keep the old behavior, but we need this migration script
otherwise.

Revision ID: 6a8c19565060
Revises: None
Create Date: 2016-03-15 23:40:11.411599
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '6a8c19565060'
down_revision = None
branch_labels = None

# pylint: disable=missing-docstring


def upgrade():
    op.rename_table('networkattachment', 'network_attachment')
    # The _id_seq is a postgres-specific thing; it has to do with the
    # AUTO INCREMENT functionality.
    op.rename_table('networkattachment_id_seq', 'network_attachment_id_seq')
    op.rename_table('networkingaction', 'networking_action')
    op.rename_table('networkingaction_id_seq', 'networking_action_id_seq')


def downgrade():
    op.rename_table('network_attachment', 'networkattachment')
    op.rename_table('network_attachment_id_seq', 'networkattachment_id_seq')
    op.rename_table('networking_action', 'networkingaction')
    op.rename_table('networking_action_id_seq', 'networkingaction_id_seq')
