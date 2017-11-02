"""Dell PK to bigint

Revision ID: b1b0e6d4302e
Revises: 099b939261c1
Create Date: 2017-07-21 14:47:33.143382

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1b0e6d4302e'
down_revision = '099b939261c1'
branch_labels = ('hil.ext.switches.dell',)

# pylint: disable=missing-docstring


def upgrade():
    op.alter_column('power_connect55xx', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT())


def downgrade():
    op.alter_column('power_connect55xx', 'id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer())
