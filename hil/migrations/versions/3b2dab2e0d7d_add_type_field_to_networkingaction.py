"""Add type field to NetworkingAction

Revision ID: 3b2dab2e0d7d
Revises: 89630e3872ec
Create Date: 2016-11-14 14:57:19.247255

"""

from alembic import op
import sqlalchemy as sa
from hil.model import NetworkingAction


# revision identifiers, used by Alembic.
revision = '3b2dab2e0d7d'
down_revision = '57f4c30b0ad4'
branch_labels = None

# pylint: disable=missing-docstring


def upgrade():
    # We first introduce the table with null 'type' fields allowed.
    # Any existing actions will have null type fields, so we then
    # update them to 'modify_port', which was previously the only
    # possible action. Then, we add the NOT NULL constraint once
    # we know it won't run afoul of any existing rows.
    op.add_column('networking_action',
                  sa.Column('type', sa.String(),
                            nullable=True))
    op.execute(sa.update(NetworkingAction).values({'type': 'modify_port'}))
    op.alter_column('networking_action', 'type', nullable=False)


def downgrade():
    op.drop_column('networking_action', 'type')
