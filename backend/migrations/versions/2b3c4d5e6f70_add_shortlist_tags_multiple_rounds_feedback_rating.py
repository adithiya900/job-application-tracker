"""add shortlist, tags, multiple interview rounds, feedback rating/strengths

Revision ID: 2b3c4d5e6f70
Revises: 1a2b3c4d5e6f
Create Date: 2026-10-08 10:36:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '2b3c4d5e6f70'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade():
    # Shortlist and tags on JobApplication
    op.add_column('job_applications', sa.Column('is_shortlisted', sa.Boolean(), nullable=False, server_default='0', index=True))
    op.add_column('job_applications', sa.Column('tags', sa.String(length=500), nullable=True))

    # Multiple interview rounds: drop unique constraint, add round_type
    # The unique constraint may already have been converted to an index by a
    # prior migration, so inspect and drop whichever form is present.
    from alembic import context
    bind = op.get_bind()
    from sqlalchemy import inspect
    inspector = inspect(bind)

    unique_constraints = inspector.get_unique_constraints('interview_details')
    constraint_names = [c['name'] for c in unique_constraints]

    if 'interview_details_application_id_key' in constraint_names:
        op.drop_constraint('interview_details_application_id_key', 'interview_details', type_='unique')
    else:
        indexes = inspector.get_indexes('interview_details')
        unique_idx = next((i for i in indexes if i['unique']), None)
        if unique_idx:
            op.drop_index(unique_idx['name'], table_name='interview_details')

    op.add_column('interview_details', sa.Column('round_type', sa.String(length=50), nullable=True))

    # Feedback rating, strengths, weaknesses, candidate_facing
    op.add_column('interview_feedback', sa.Column('rating', sa.Integer(), nullable=True))
    op.add_column('interview_feedback', sa.Column('strengths', sa.Text(), nullable=True))
    op.add_column('interview_feedback', sa.Column('weaknesses', sa.Text(), nullable=True))
    op.add_column('interview_feedback', sa.Column('candidate_facing', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('interview_feedback', sa.Column('candidate_facing_summary', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('interview_feedback', 'candidate_facing_summary')
    op.drop_column('interview_feedback', 'candidate_facing')
    op.drop_column('interview_feedback', 'weaknesses')
    op.drop_column('interview_feedback', 'strengths')
    op.drop_column('interview_feedback', 'rating')

    op.drop_column('interview_details', 'round_type')
    op.create_unique_constraint('interview_details_application_id_key', 'interview_details', ['application_id'])

    op.drop_column('job_applications', 'tags')
    op.drop_column('job_applications', 'is_shortlisted')
