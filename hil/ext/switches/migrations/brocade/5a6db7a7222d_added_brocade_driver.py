"""Added Brocade driver

Revision ID: 5a6db7a7222d
Revises: 6a8c19565060
Create Date: 2016-04-11 16:26:40.715332

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5a6db7a7222d'
down_revision = None
branch_labels = None

# pylint: disable=missing-docstring


def upgrade():
    op.create_table(
        'brocade',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=False),
        sa.Column('hostname', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('interface_type', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('brocade')
