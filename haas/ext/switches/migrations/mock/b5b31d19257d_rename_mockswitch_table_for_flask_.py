"""Rename mockswitch table for Flask-SQLAlchemy

Revision ID: b5b31d19257d
Revises:
Create Date: 2016-03-22 05:11:19.585905

"""

# revision identifiers, used by Alembic.
revision = 'b5b31d19257d'
down_revision = None
branch_labels = ('haas.ext.switches.mock',)

from alembic import op
import sqlalchemy as sa
from haas.model import db
from haas.flaskapp import app


def upgrade():
    metadata = sa.MetaData(bind=db.get_engine(app), reflect=True)
    if 'mockswitch' in metadata.tables:
        op.rename_table('mockswitch', 'mock_switch')


def downgrade():
    op.rename_table('mock_switch', 'mockswitch')
