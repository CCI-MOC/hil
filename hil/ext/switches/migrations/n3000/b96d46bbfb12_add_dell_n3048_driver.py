"""Add Dell N3048 Driver

Revision ID: b96d46bbfb12
Revises: 3b2dab2e0d7d
Create Date: 2017-06-08 22:04:10.197640

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b96d46bbfb12'
down_revision = None
branch_labels = None

# pylint: disable=missing-docstring


def upgrade():
    op.create_table('dell_n3000',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('hostname', sa.String(), nullable=False),
                    sa.Column('username', sa.String(), nullable=False),
                    sa.Column('password', sa.String(), nullable=False),
                    sa.Column('dummy_vlan', sa.String(), nullable=False),
                    sa.ForeignKeyConstraint(['id'], ['switch.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('dell_n3000')
