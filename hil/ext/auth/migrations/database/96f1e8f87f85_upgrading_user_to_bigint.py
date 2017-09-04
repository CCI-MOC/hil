"""upgrading User to bigint

Revision ID: 96f1e8f87f85
Revises: cb7096e21dfb
Create Date: 2017-07-12 16:24:27.897244

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '96f1e8f87f85'
down_revision = None
branch_labels = ('hil.ext.auth.database',)

# pylint: disable=missing-docstring


def upgrade():
    op.alter_column(
        'user',
        'id',
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        autoincrement=True,
        existing_server_default=sa.text(u"nextval('user_id_seq'::regclass)"))
    op.alter_column('user_projects', 'user_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=True)
    op.alter_column('user_projects', 'project_id',
                    existing_type=sa.Integer(),
                    type_=sa.BIGINT(),
                    existing_nullable=True)


def downgrade():
    op.alter_column(
        'user',
        'id',
        existing_type=sa.BIGINT(),
        type_=sa.Integer(),
        autoincrement=True,
        existing_server_default=sa.text(u"nextval('user_id_seq'::regclass)"))
    op.alter_column('user_projects', 'user_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column('user_projects', 'project_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.Integer(),
                    existing_nullable=True)
