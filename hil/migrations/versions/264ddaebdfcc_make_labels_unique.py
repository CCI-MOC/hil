"""make labels unique

Revision ID: 264ddaebdfcc
Revises: 89ff8a6d72b2
Create Date: 2018-03-12 11:15:09.729850

"""

from alembic import op
# import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '264ddaebdfcc'
down_revision = '89ff8a6d72b2'
branch_labels = ('hil')

# pylint: disable=missing-docstring


def upgrade():
    op.create_unique_constraint(None, 'network', ['label'])
    op.create_unique_constraint(None, 'node', ['label'])
    op.create_unique_constraint(None, 'project', ['label'])
    op.create_unique_constraint(None, 'switch', ['label'])


def downgrade():
    op.drop_constraint(None, 'switch', type_='unique')
    op.drop_constraint(None, 'project', type_='unique')
    op.drop_constraint(None, 'node', type_='unique')
    op.drop_constraint(None, 'network', type_='unique')
