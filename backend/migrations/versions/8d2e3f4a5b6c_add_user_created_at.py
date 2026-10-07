"""Add user registration and account-status fields.

Revision ID: 8d2e3f4a5b6c
Revises: 4698298baae9, 7e8ee8478894
Create Date: 2026-06-12 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "8d2e3f4a5b6c"
down_revision = ("4698298baae9", "7e8ee8478894")
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade():
    op.drop_column("users", "is_active")
    op.drop_column("users", "created_at")
