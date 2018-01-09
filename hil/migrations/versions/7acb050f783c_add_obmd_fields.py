"""Add obmd fields

Revision ID: 7acb050f783c
Revises: 9089fa811a2b
Create Date: 2018-01-09 18:29:58.413692

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7acb050f783c'
down_revision = '9089fa811a2b'
branch_labels = ('hil',)

# pylint: disable=missing-docstring


def upgrade():
    op.add_column(
        'node',
        sa.Column('obmd_admin_token', sa.String(), nullable=True),
    )
    op.add_column(
        'node',
        sa.Column('obmd_node_token', sa.String(), nullable=True),
    )
    op.add_column(
        'node',
        sa.Column('obmd_uri', sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column('node', 'obmd_admin_token')
    op.drop_column('node', 'obmd_node_token')
    op.drop_column('node', 'obmd_uri')
