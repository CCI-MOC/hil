"""mark obmd fields not nullable

Revision ID: d65a9dc873d7
Revises: 264ddaebdfcc
Create Date: 2018-04-07 19:10:35.243712

"""

import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from hil import model


# revision identifiers, used by Alembic.
revision = 'd65a9dc873d7'
down_revision = '264ddaebdfcc'
branch_labels = ('hil',)

# pylint: disable=missing-docstring


def upgrade():
    if os.getenv('SPOOF_MANUAL_MIGRATIONS') == 'true':
        # The normal upgrade process requires an admin to run a helper
        # script that we've written, which exports node info to OBMd,
        # and adds the relevant fields. In the test suite, we don't have
        # the opportunity to do this, so we expose (via an environment
        # variable) the ability to spoof the data, so that the tests can
        # pass.
        conn = op.get_bind()
        session = Session(bind=conn)
        for node in session.query(model.Node):
            # If we're in the test, we should expect that neither of these
            # has been set:
            assert node.obmd_uri is None
            assert node.obmd_admin_token is None

            node.obmd_uri = 'http://obmd.example.com/nodes/' + node.label
            node.obmd_admin_token = 'secret'

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
