"""N3000 PK to bigint

Revision ID: 357bcff65fb3
Revises: b96d46bbfb12
Create Date: 2017-07-21 16:17:47.356052

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '357bcff65fb3'
down_revision = 'b96d46bbfb12'
branch_labels = ('hil.ext.switches.n3000',)

# pylint: disable=missing-docstring


def upgrade():
    op.alter_column('dell_n3000', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT())


def downgrade():
    op.alter_column('dell_n3000', 'id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer())
