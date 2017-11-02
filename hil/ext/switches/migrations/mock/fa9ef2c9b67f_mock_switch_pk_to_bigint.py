"""mock switch PK to bigint

Revision ID: fa9ef2c9b67f
Revises: b5b31d19257d
Create Date: 2017-07-24 15:46:29.332253

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa9ef2c9b67f'
down_revision = 'b5b31d19257d'
branch_labels = ('hil.ext.switches.mock',)

# pylint: disable=missing-docstring


def upgrade():
    op.alter_column('mock_switch', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT())


def downgrade():
    op.alter_column('mock_switch', 'id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer())
