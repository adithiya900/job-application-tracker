"""merge migration heads

Revision ID: 4698298baae9
Revises: 6152186d3488,a1b2c3d4e5f7
Create Date: 2026-10-05 16:47:37.650352

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4698298baae9'
down_revision = ('6152186d3488', 'a1b2c3d4e5f7')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
