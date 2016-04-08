"""Rename mockobm table for flask

See the docstring in 'haas/migrations/versions/6a8c19565060_move_to_flask.py'

Revision ID: df8d9f423f2b
Revises: 6a8c19565060
Create Date: 2016-04-04 02:24:53.812100

"""

# revision identifiers, used by Alembic.
revision = 'df8d9f423f2b'
down_revision = None
branch_labels = ('haas.ext.obm.mock',)

from alembic import op
import sqlalchemy as sa
from haas.model import db
from haas.flaskapp import app


def upgrade():
    metadata = sa.MetaData(bind=db.get_engine(app), reflect=True)
    if 'mockobm' in metadata.tables:
        op.rename_table('mockobm', 'mock_obm')


def downgrade():
    op.rename_table('mock_obm', 'mockobm')
