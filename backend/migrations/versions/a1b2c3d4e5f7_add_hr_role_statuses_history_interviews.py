"""Add HR role, new statuses, status history, interview details, feedback tables

Revision ID: a1b2c3d4e5f7
Revises: f1b2c3d4e5f6
Create Date: 2026-10-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = 'f1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # =============================================
    # 1. Add HR to the role enum
    # =============================================
    # PostgreSQL requires ALTER TYPE to add new enum values
    op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'HR'")

    # =============================================
    # 2. Add UNDER_REVIEW and WITHDRAWN to applicationstatus enum
    # =============================================
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'UNDER_REVIEW'")
    op.execute("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'WITHDRAWN'")

    # =============================================
    # 3. Create application_status_history table
    # =============================================
    op.create_table(
        'application_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('old_status', sa.Enum(
            'APPLIED', 'UNDER_REVIEW', 'PHONE_SCREEN', 'INTERVIEW',
            'OFFER', 'REJECTED', 'WITHDRAWN',
            name='applicationstatus'
        ), nullable=True),
        sa.Column('new_status', sa.Enum(
            'APPLIED', 'UNDER_REVIEW', 'PHONE_SCREEN', 'INTERVIEW',
            'OFFER', 'REJECTED', 'WITHDRAWN',
            name='applicationstatus'
        ), nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_application_status_history_application_id', 'application_status_history', ['application_id'])
    op.create_index('ix_application_status_history_changed_at', 'application_status_history', ['changed_at'])

    # =============================================
    # 4. Create interview_details table
    # =============================================
    op.create_table(
        'interview_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('interview_date', sa.Date(), nullable=True),
        sa.Column('interview_time', sa.String(length=10), nullable=True),
        sa.Column('interview_round', sa.String(length=100), nullable=True),
        sa.Column('interview_type', sa.String(length=50), nullable=True),
        sa.Column('meeting_link', sa.String(length=500), nullable=True),
        sa.Column('interviewer', sa.String(length=200), nullable=True),
        sa.Column('hr_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id')
    )
    op.create_index('ix_interview_details_application_id', 'interview_details', ['application_id'])

    # =============================================
    # 5. Create interview_feedback table
    # =============================================
    op.create_table(
        'interview_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('submitted_by', sa.Integer(), nullable=True),
        sa.Column('technical_skills', sa.String(length=50), nullable=True),
        sa.Column('communication', sa.String(length=50), nullable=True),
        sa.Column('overall_feedback', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.String(length=50), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submitted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_interview_feedback_application_id', 'interview_feedback', ['application_id'])


def downgrade():
    op.drop_table('interview_feedback')
    op.drop_table('interview_details')
    op.drop_table('application_status_history')
    # Note: PostgreSQL does not support removing enum values easily.
    # The enum values UNDER_REVIEW, WITHDRAWN, and HR role remain.
