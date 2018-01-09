"""add uuid and status to NetworkingAction

Revision ID: 76529f0f9e50
Revises: 9089fa811a2b
Create Date: 2018-01-07 15:24:09.545021

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '76529f0f9e50'
down_revision = '9089fa811a2b'
branch_labels = None

# pylint: disable=missing-docstring


def upgrade():
    op.add_column('networking_action', sa.Column('status', sa.String(),
                  nullable=True))
    op.add_column('networking_action', sa.Column('uuid', sa.String(),
                  nullable=True))
    op.create_index(op.f('ix_networking_action_uuid'), 'networking_action',
                    ['uuid'], unique=False)
    op.execute("UPDATE networking_action SET status = 'PENDING', \
        uuid ='no-uuid'")
    op.alter_column('networking_action', 'status', nullable=False)
    op.alter_column('networking_action', 'uuid', nullable=False)


def downgrade():
    op.drop_index(op.f('ix_networking_action_uuid'),
                  table_name='networking_action')
    op.drop_column('networking_action', 'uuid')
    op.drop_column('networking_action', 'status')
