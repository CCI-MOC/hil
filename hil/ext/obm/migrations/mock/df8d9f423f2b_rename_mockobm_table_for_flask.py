"""Rename mockobm table for flask

See the docstring in 'hil/migrations/versions/6a8c19565060_move_to_flask.py'

Revision ID: df8d9f423f2b
Revises: 6a8c19565060
Create Date: 2016-04-04 02:24:53.812100

"""
from alembic import op
from hil.model import db

# revision identifiers, used by Alembic.
revision = 'df8d9f423f2b'
down_revision = None
branch_labels = None

# pylint: disable=missing-docstring


def upgrade():
    metadata = db.inspect(db.engine).get_table_names()
    if 'mockobm' in metadata:
        op.rename_table('mockobm', 'mock_obm')


def downgrade():
    op.rename_table('mock_obm', 'mockobm')
