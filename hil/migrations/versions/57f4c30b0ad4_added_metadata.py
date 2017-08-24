"""added metadata

Revision ID: 57f4c30b0ad4
Revises: 89630e3872ec
Create Date: 2016-11-08 08:36:01.183860

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '57f4c30b0ad4'
down_revision = '89630e3872ec'
branch_labels = None

# pylint: disable=missing-docstring


def upgrade():
    op.create_table('metadata',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('label', sa.String(), nullable=False),
                    sa.Column('value', sa.String(), nullable=True),
                    sa.Column('owner_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['owner_id'], ['node.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('metadata')
