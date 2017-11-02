"""ipmi obm Pks to bigint

Revision ID: fcb23cd2e9b7
Revises: 9089fa811a2b
Create Date: 2017-07-21 11:47:26.250168

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fcb23cd2e9b7'
down_revision = None
branch_labels = ('hil.ext.obm.ipmi',)

# pylint: disable=missing-docstring


def upgrade():
    op.alter_column('ipmi', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT())


def downgrade():
    op.alter_column('ipmi', 'id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer())
