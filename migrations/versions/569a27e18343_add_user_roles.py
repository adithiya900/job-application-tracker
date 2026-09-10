"""Add user roles

Revision ID: 569a27e18343
Revises: da10fc7a663e
Create Date: 2026-09-10 12:37:47.978889

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '569a27e18343'
down_revision = 'da10fc7a663e'
branch_labels = None
depends_on = None


def upgrade():
    
    role_enum = sa.Enum(
        'USER',
        'ADMIN',
        name='role'
    )

    role_enum.create(
        op.get_bind(),
        checkfirst=True
    )

    with op.batch_alter_table(
        'users',
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                'role',
                role_enum,
                nullable=False,
                server_default='USER'
            )
        )

    with op.batch_alter_table(
        'users',
        schema=None
    ) as batch_op:

        batch_op.alter_column(
            'role',
            server_default=None
        )
 
   


def downgrade():
    with op.batch_alter_table(
        'users',
        schema=None
    ) as batch_op:

        batch_op.drop_column('role')

    sa.Enum(
        'USER',
        'ADMIN',
        name='role'
    ).drop(
        op.get_bind(),
        checkfirst=True
    )
   