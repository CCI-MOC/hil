"""vlan_pool PK to bigint

Revision ID: e06576b2ea9e
Revises: 9089fa811a2b
Create Date: 2017-07-21 16:34:50.005560

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e06576b2ea9e'
down_revision = None
branch_labels = ('hil.ext.network_allocators.vlan_pool',)

# pylint: disable=missing-docstring


def upgrade():
    op.alter_column('vlan', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT())


def downgrade():
    op.alter_column('vlan', 'id',
                    existing_type=sa.BIGINT(),
                    type_=sa.INTEGER())
