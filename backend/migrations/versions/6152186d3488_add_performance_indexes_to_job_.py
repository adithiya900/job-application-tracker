"""Add performance indexes to job applications

Revision ID: 6152186d3488
Revises: f1b2c3d4e5f6
Create Date: 2026-09-18 11:29:58.805356

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "6152186d3488"
down_revision = "f1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("job_applications", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_job_applications_applied_date"),
            ["applied_date"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_job_applications_status"),
            ["status"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_job_applications_user_id"),
            ["user_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("job_applications", schema=None) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_job_applications_user_id")
        )
        batch_op.drop_index(
            batch_op.f("ix_job_applications_status")
        )
        batch_op.drop_index(
            batch_op.f("ix_job_applications_applied_date")
        )