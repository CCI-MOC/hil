"""Delete legacy obm support

Revision ID: 02f7e9607e16
Revises: d65a9dc873d7
Create Date: 2018-09-04 17:00:44.359952

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '02f7e9607e16'
down_revision = 'd65a9dc873d7'
branch_labels = ('hil',)

# pylint: disable=missing-docstring


def upgrade():
    engine = op.get_bind()

    # These tables may or may not exist, depending on what extensions the user
    # had enabled:
    for driver_table in 'mock_obm', 'ipmi':
        if engine.dialect.has_table(engine, driver_table):
            op.drop_table(driver_table)

    op.drop_constraint(u'node_obm_id_fkey', 'node', type_='foreignkey')
    op.drop_column('node', 'obm_id')
    op.drop_table('obm')


def downgrade():
    op.create_table(
        'obm',
        sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column('type', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('id', name=u'obm_pkey')
    )

    op.add_column(
        'node',
        sa.Column('obm_id', sa.BIGINT(), autoincrement=False, nullable=False),
    )
    op.create_foreign_key(
        u'node_obm_id_fkey', 'node', 'obm', ['obm_id'], ['id'],
    )
