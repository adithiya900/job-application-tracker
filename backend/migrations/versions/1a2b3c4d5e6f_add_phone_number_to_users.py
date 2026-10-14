"""add phone_number to users

Revision ID: 1a2b3c4d5e6f
Revises: f5f927bcb434_rename_phone_screen_to_phone_call_
Create Date: 2026-10-08 10:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '1a2b3c4d5e6f'
down_revision = 'f5f927bcb434'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(length=30), nullable=True))


def downgrade():
    op.drop_column('users', 'phone_number')
