"""core PKs to bigint

Revision ID: 9089fa811a2b
Revises: a2c6bf79f41c
Create Date: 2017-07-21 10:37:40.944716

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9089fa811a2b'
down_revision = 'c45f6a96dbe7'
branch_labels = ('hil',)

# pylint: disable=missing-docstring


def downgrade():
    op.alter_column(
        'headnode',
        'id',
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        autoincrement=True,
        existing_server_default=sa.text(
            u"nextval('headnode_id_seq'::regclass)"))
    op.alter_column('headnode', 'project_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=False)
    op.alter_column('hnic', 'id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    autoincrement=True)
    op.alter_column('hnic', 'network_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column('hnic', 'owner_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=False)
    op.alter_column('metadata', 'id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    autoincrement=True)
    op.alter_column('metadata', 'owner_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=False)
    op.alter_column(
        'network',
        'id',
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        autoincrement=True,
        existing_server_default=sa.text(
            u"nextval('network_id_seq'::regclass)"))
    op.alter_column('network', 'owner_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column('network_attachment', 'id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    autoincrement=True)
    op.alter_column('network_attachment', 'network_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=False)
    op.alter_column('network_attachment', 'nic_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=False)
    op.alter_column('network_projects', 'network_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column('network_projects', 'project_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column('networking_action', 'id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    autoincrement=True)
    op.alter_column('networking_action', 'new_network_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column('networking_action', 'nic_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=False)
    op.alter_column(
        'nic',
        'id',
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        autoincrement=True,
        existing_server_default=sa.text(u"nextval('nic_id_seq'::regclass)"))
    op.alter_column('nic', 'owner_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=False)
    op.alter_column('nic', 'port_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column(
        'node',
        'id',
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        autoincrement=True,
        existing_server_default=sa.text(u"nextval('node_id_seq'::regclass)"))
    op.alter_column('node', 'obm_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=False)
    op.alter_column('node', 'project_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column('obm', 'id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    autoincrement=True)
    op.alter_column(
        'port',
        'id',
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        autoincrement=True,
        existing_server_default=sa.text(u"nextval('port_id_seq'::regclass)"))
    op.alter_column('port', 'owner_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=False)
    op.alter_column(
        'project',
        'id',
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        autoincrement=True,
        existing_server_default=sa.text(
            u"nextval('project_id_seq'::regclass)"))
    op.alter_column(
        'switch',
        'id',
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        autoincrement=True,
        existing_server_default=sa.text(u"nextval('switch_id_seq'::regclass)"))


def upgrade():
    op.alter_column(
        'switch',
        'id',
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        autoincrement=True,
        existing_server_default=sa.text(u"nextval('switch_id_seq'::regclass)"))
    op.alter_column(
        'project',
        'id',
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        autoincrement=True,
        existing_server_default=sa.text(
            u"nextval('project_id_seq'::regclass)"))
    op.alter_column('port', 'owner_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)
    op.alter_column(
        'port',
        'id',
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        autoincrement=True,
        existing_server_default=sa.text(u"nextval('port_id_seq'::regclass)"))
    op.alter_column('obm', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    autoincrement=True)
    op.alter_column('node', 'project_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=True)
    op.alter_column('node', 'obm_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)
    op.alter_column(
        'node',
        'id',
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        autoincrement=True,
        existing_server_default=sa.text(u"nextval('node_id_seq'::regclass)"))
    op.alter_column('nic', 'port_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=True)
    op.alter_column('nic', 'owner_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)
    op.alter_column(
        'nic',
        'id',
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        autoincrement=True,
        existing_server_default=sa.text(u"nextval('nic_id_seq'::regclass)"))
    op.alter_column('networking_action', 'nic_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)
    op.alter_column('networking_action', 'new_network_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=True)
    op.alter_column('networking_action', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    autoincrement=True)
    op.alter_column('network_projects', 'project_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=True)
    op.alter_column('network_projects', 'network_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=True)
    op.alter_column('network_attachment', 'nic_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)
    op.alter_column('network_attachment', 'network_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)
    op.alter_column('network_attachment', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    autoincrement=True)
    op.alter_column('network', 'owner_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=True)
    op.alter_column(
        'network',
        'id',
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        autoincrement=True,
        existing_server_default=sa.text(
            u"nextval('network_id_seq'::regclass)"))
    op.alter_column('metadata', 'owner_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)
    op.alter_column('metadata', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    autoincrement=True)
    op.alter_column('hnic', 'owner_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)
    op.alter_column('hnic', 'network_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=True)
    op.alter_column('hnic', 'id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    autoincrement=True)
    op.alter_column('headnode', 'project_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)
    op.alter_column(
        'headnode',
        'id',
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        autoincrement=True,
        existing_server_default=sa.text(
            u"nextval('headnode_id_seq'::regclass)"))
