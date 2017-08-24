"""Brocade PK to bigint

Revision ID: 03ae4ec647da
Revises: 5a6db7a7222d
Create Date: 2017-07-21 15:19:36.049634

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '03ae4ec647da'
down_revision = '5a6db7a7222d'
branch_labels = ('hil.ext.switches.brocade',)

# pylint: disable=missing-docstring


def upgrade():
    op.alter_column('brocade', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT())


def downgrade():
    op.alter_column('brocade', 'id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer())
