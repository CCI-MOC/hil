"""Rename dell switch table for Flask-SQLAlchemy

See the docstring in 'hil/migrations/versions/6a8c19565060_move_to_flask.py'

Revision ID: 099b939261c1
Revises:
Create Date: 2016-03-22 04:34:49.141555

"""
from alembic import op
from hil.model import db

# revision identifiers, used by Alembic.
revision = '099b939261c1'
down_revision = None
branch_labels = None

# pylint: disable=missing-docstring


def upgrade():
    db.session.close()
    metadata = db.inspect(db.engine).get_table_names()
    if 'powerconnect55xx' in metadata:
        op.rename_table('powerconnect55xx', 'power_connect55xx')


def downgrade():
    op.rename_table('power_connect55xx', 'powerconnect55xx')
