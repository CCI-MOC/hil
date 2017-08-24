"""mock obm PKs to bigint

Revision ID: 655e037522d0
Revises: df8d9f423f2b
Create Date: 2017-07-21 11:24:18.746152

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '655e037522d0'
down_revision = 'df8d9f423f2b'
branch_labels = ('hil.ext.obm.mock',)

# pylint: disable=missing-docstring


def upgrade():

    op.alter_column('mock_obm', 'id',
                    existing_type=sa.INTEGER(),
                    type_=sa.BigInteger())


def downgrade():
    op.alter_column('mock_obm', 'id',
                    existing_type=sa.BigInteger(),
                    type_=sa.INTEGER())
