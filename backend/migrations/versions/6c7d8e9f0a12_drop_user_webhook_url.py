"""drop user slack webhook url

Revision ID: 6c7d8e9f0a12
Revises: 5b6c7d8e9f01
Create Date: 2026-10-13 07:00:00.000000

Removes the users.webhook_url column added by 7e8ee8478894. It only stored the
Slack Webhook URL and its Slack notification flow, both of which are deleted.
The generic WEBHOOK_URL / WEBHOOK_SECRET status-change integration is separate
and untouched.
"""

from alembic import op
import sqlalchemy as sa


revision = '6c7d8e9f0a12'
down_revision = '5b6c7d8e9f01'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    existing = {
        row[0]
        for row in bind.exec_driver_sql(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'users'"
        ).fetchall()
    }
    if 'webhook_url' in existing:
        op.drop_column('users', 'webhook_url')


def downgrade():
    bind = op.get_bind()
    existing = {
        row[0]
        for row in bind.exec_driver_sql(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'users'"
        ).fetchall()
    }
    if 'webhook_url' not in existing:
        op.add_column(
            'users',
            sa.Column('webhook_url', sa.String(length=500), nullable=True)
        )
