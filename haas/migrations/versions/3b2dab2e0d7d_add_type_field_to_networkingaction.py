"""Add type field to NetworkingAction

Revision ID: 3b2dab2e0d7d
Revises: 89630e3872ec
Create Date: 2016-11-14 14:57:19.247255

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b2dab2e0d7d'
down_revision = '57f4c30b0ad4'
branch_labels = ('haas',)


def upgrade():
    op.add_column('networking_action',
                  sa.Column('type', sa.String(),
                            nullable=False))


def downgrade():
    op.drop_column('networking_action', 'type')
