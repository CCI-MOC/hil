"""Rename mockswitch table for Flask-SQLAlchemy

See the docstring in 'hil/migrations/versions/6a8c19565060_move_to_flask.py'

Revision ID: b5b31d19257d
Revises:
Create Date: 2016-03-22 05:11:19.585905

"""
from alembic import op
from hil.model import db

# revision identifiers, used by Alembic.
revision = 'b5b31d19257d'
down_revision = None
branch_labels = None

# pylint: disable=missing-docstring


def upgrade():
    metadata = db.inspect(db.engine).get_table_names()
    if 'mockswitch' in metadata:
        op.rename_table('mockswitch', 'mock_switch')


def downgrade():
    op.rename_table('mock_switch', 'mockswitch')
