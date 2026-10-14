"""create follow_up_reminders table

Revision ID: 3c4d5e6f70a1
Revises: 2b3c4d5e6f70
Create Date: 2026-10-08 10:37:00.000000

"""
from alembic import op
import sqlalchemy as sa
import enum


revision = '3c4d5e6f70a1'
down_revision = '2b3c4d5e6f70'
branch_labels = None
depends_on = None


# Define enums for raw SQL usage
def _reminder_type_enum():
    return sa.Enum('PHONE_CALL', 'INTERVIEW', 'FOLLOW_UP', 'CUSTOM', name='remindertype')

def _reminder_status_enum():
    return sa.Enum('PENDING', 'SENT', 'FAILED', 'DISMISSED', name='reminderstatus')


def upgrade():
    bind = op.get_bind()

    # Create enums only if they don't already exist (avoids DuplicateObject)
    existing_types = bind.exec_driver_sql(
        "SELECT typname FROM pg_type WHERE typname IN ('remindertype', 'reminderstatus')"
    ).fetchall()
    existing_type_names = [t[0] for t in existing_types]

    if 'remindertype' not in existing_type_names:
        bind.exec_driver_sql(
            "CREATE TYPE remindertype AS ENUM ('PHONE_CALL', 'INTERVIEW', 'FOLLOW_UP', 'CUSTOM')"
        )
    if 'reminderstatus' not in existing_type_names:
        bind.exec_driver_sql(
            "CREATE TYPE reminderstatus AS ENUM ('PENDING', 'SENT', 'FAILED', 'DISMISSED')"
        )

    # Create table with raw SQL to avoid SQLAlchemy re-creating the enum types
    bind.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS follow_up_reminders (
            id SERIAL PRIMARY KEY,
            application_id INTEGER NOT NULL REFERENCES job_applications(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_by_hr_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            reminder_type remindertype NOT NULL DEFAULT 'FOLLOW_UP',
            message TEXT,
            scheduled_at TIMESTAMP NOT NULL,
            lead_time_minutes INTEGER DEFAULT 0,
            status reminderstatus NOT NULL DEFAULT 'PENDING',
            sent_at TIMESTAMP,
            dismissed BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    bind.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_follow_up_reminders_application_id ON follow_up_reminders (application_id)")
    bind.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_follow_up_reminders_user_id ON follow_up_reminders (user_id)")
    bind.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_follow_up_reminders_status ON follow_up_reminders (status)")


def downgrade():
    op.drop_table('follow_up_reminders')
    bind = op.get_bind()
    bind.exec_driver_sql("DROP TYPE IF EXISTS reminderstatus")
    bind.exec_driver_sql("DROP TYPE IF EXISTS remindertype")
