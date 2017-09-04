"""NIC primary key changed to BIGINT

Revision ID: c45f6a96dbe7
Revises: 3b2dab2e0d7d
Create Date: 2017-06-14 10:36:17.744991

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c45f6a96dbe7'
down_revision = '3b2dab2e0d7d'
branch_labels = None

# pylint: disable=missing-docstring


def upgrade():
    op.alter_column(
        'nic',
        'id',
        existing_type=sa.INTEGER(),
        type_=sa.BIGINT(),
        autoincrement=True,
        existing_server_default=sa.text(u"nextval('nic_id_seq'::regclass)"))
    op.alter_column('networking_action', 'nic_id',
                    existing_type=sa.INTEGER(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)
    op.alter_column('network_attachment', 'nic_id',
                    existing_type=sa.INTEGER(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)


def downgrade():
    op.alter_column('network_attachment', 'nic_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.INTEGER(),
                    existing_nullable=False)
    op.alter_column('networking_action', 'nic_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.INTEGER(),
                    existing_nullable=False)
    op.alter_column(
        'nic',
        'id',
        existing_type=sa.BIGINT(),
        type_=sa.INTEGER(),
        autoincrement=True,
        existing_server_default=sa.text(u"nextval('nic_id_seq'::regclass)"))
