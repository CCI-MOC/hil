"""Nexus PKs to bigint

Revision ID: 09d96bf567aa
Revises: 9089fa811a2b
Create Date: 2017-07-21 15:43:24.005782

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '09d96bf567aa'
down_revision = None
branch_labels = ('hil.ext.switches.nexus',)

# pylint: disable=missing-docstring


def upgrade():
    op.alter_column('nexus', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT())


def downgrade():
    op.alter_column('nexus', 'id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer())
