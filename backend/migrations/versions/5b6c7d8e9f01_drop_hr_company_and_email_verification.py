"""drop hr company and email verification tables

Revision ID: 5b6c7d8e9f01
Revises: 3c4d5e6f70a1
Create Date: 2026-10-12 10:30:00.000000

Reverses the HR self-registration / company-verification feature: the
company_verifications, verification_decisions and
email_verification_challenges tables and the users.email_verified columns
are removed, and HR access is granted purely by role again.

Migrations that already applied the original change should set their
alembic_version back to '3c4d5e6f70a1' before running this revision.
"""

from alembic import op


revision = '5b6c7d8e9f01'
down_revision = '3c4d5e6f70a1'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    bind.exec_driver_sql("DROP TABLE IF EXISTS verification_decisions")
    bind.exec_driver_sql("DROP TABLE IF EXISTS company_verifications")
    bind.exec_driver_sql("DROP TABLE IF EXISTS email_verification_challenges")

    bind.exec_driver_sql("ALTER TABLE users DROP COLUMN IF EXISTS email_verified_at")
    bind.exec_driver_sql("ALTER TABLE users DROP COLUMN IF EXISTS email_verified")

    for name in (
        'emailverificationpurpose',
        'verificationaction',
        'companyverificationstatus',
    ):
        bind.exec_driver_sql(f"DROP TYPE IF EXISTS {name}")


def downgrade():
    # The HR verification schema was intentionally removed; restoring it is
    # not supported. Re-add the feature and its migration if it is needed
    # again.
    raise NotImplementedError(
        "Re-creating the HR verification schema is not supported."
    )
