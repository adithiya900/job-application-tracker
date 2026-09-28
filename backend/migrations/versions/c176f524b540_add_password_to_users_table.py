"""Add password to users table

Revision ID: c176f524b540
Revises: 86adf6e9e730
Create Date: 2026-09-02 12:23:19.620130

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c176f524b540"
down_revision = "86adf6e9e730"
branch_labels = None
depends_on = None


def upgrade():

    # Step 1: Add password column temporarily allowing NULL
    op.add_column(
        "users",
        sa.Column(
            "password",
            sa.String(length=255),
            nullable=True
        )
    )

    # Step 2: Give existing users a temporary password value
    op.execute(
        "UPDATE users SET password = 'CHANGE_ME' WHERE password IS NULL"
    )

    # Step 3: Make password NOT NULL
    op.alter_column(
        "users",
        "password",
        existing_type=sa.String(length=255),
        nullable=False
    )


def downgrade():

    op.drop_column("users", "password")