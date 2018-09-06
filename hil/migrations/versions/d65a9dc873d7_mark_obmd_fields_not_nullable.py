"""mark obmd fields not nullable

Revision ID: d65a9dc873d7
Revises: aa9106430f1c
Create Date: 2018-04-07 19:10:35.243712

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd65a9dc873d7'
down_revision = 'aa9106430f1c'
branch_labels = None

# pylint: disable=missing-docstring


def upgrade():
    op.alter_column(
        'node',
        'obmd_admin_token',
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
    op.alter_column(
        'node',
        'obmd_uri',
        existing_type=sa.VARCHAR(),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        'node',
        'obmd_uri',
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.alter_column(
        'node',
        'obmd_admin_token',
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
