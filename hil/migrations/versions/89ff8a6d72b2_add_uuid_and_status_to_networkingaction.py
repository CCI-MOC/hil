"""add uuid and status to networkingaction

Revision ID: 89ff8a6d72b2
Revises: 7acb050f783c
Create Date: 2018-01-18 14:04:09.553012

"""

from alembic import op
from sqlalchemy.orm import Session
import sqlalchemy as sa
import uuid
from hil import model

# revision identifiers, used by Alembic.
revision = '89ff8a6d72b2'
down_revision = '7acb050f783c'
branch_labels = ('hil',)

# pylint: disable=missing-docstring


def upgrade():
    op.add_column('networking_action', sa.Column('status', sa.String(),
                  nullable=True))
    op.add_column('networking_action', sa.Column('uuid', sa.String(),
                  nullable=True))
    op.create_index(op.f('ix_networking_action_uuid'), 'networking_action',
                    ['uuid'], unique=False)

    conn = op.get_bind()
    session = Session(bind=conn)
    for item in session.query(model.NetworkingAction):
        item.uuid = str(uuid.uuid4())
        item.status = 'PENDING'
    session.commit()
    session.close()

    op.alter_column('networking_action', 'status', nullable=False)
    op.alter_column('networking_action', 'uuid', nullable=False)


def downgrade():
    op.execute("DELETE from networking_action "
               "WHERE status = 'DONE' or status = 'ERROR'")
    op.drop_index(op.f('ix_networking_action_uuid'),
                  table_name='networking_action')
    op.drop_column('networking_action', 'uuid')
    op.drop_column('networking_action', 'status')
