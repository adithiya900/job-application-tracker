"""Add audit logs and user delete cascades

Revision ID: f1b2c3d4e5f6
Revises: 569a27e18343
Create Date: 2026-09-10 15:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f1b2c3d4e5f6"
down_revision = "569a27e18343"
branch_labels = None
depends_on = None


def _replace_user_foreign_key(table_name, ondelete, constraint_name):
    bind = op.get_bind()

    if bind.dialect.name == "sqlite":
        naming_convention = {
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
        }
        with op.batch_alter_table(
            table_name,
            naming_convention=naming_convention
        ) as batch_op:
            batch_op.drop_constraint(
                f"fk_{table_name}_user_id_users",
                type_="foreignkey"
            )
            batch_op.create_foreign_key(
                f"fk_{table_name}_user_id_users",
                "users",
                ["user_id"],
                ["id"],
                ondelete=ondelete
            )
    else:
        op.drop_constraint(
            constraint_name,
            table_name,
            type_="foreignkey"
        )
        op.create_foreign_key(
            f"fk_{table_name}_user_id_users",
            table_name,
            "users",
            ["user_id"],
            ["id"],
            ondelete=ondelete
        )


def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    _replace_user_foreign_key(
        "job_applications",
        "CASCADE",
        "job_applications_user_id_fkey"
    )
    _replace_user_foreign_key(
        "token_blocklist",
        "CASCADE",
        "token_blocklist_user_id_fkey"
    )


def downgrade():
    op.drop_table("audit_logs")
    _replace_user_foreign_key(
        "job_applications",
        None,
        "fk_job_applications_user_id_users"
    )
    _replace_user_foreign_key(
        "token_blocklist",
        None,
        "fk_token_blocklist_user_id_users"
    )
