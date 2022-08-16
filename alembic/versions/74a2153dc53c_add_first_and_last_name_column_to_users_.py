"""add_first_and_last_name_column_to_users_table

Revision ID: 74a2153dc53c
Revises: 60ea7a034f6e
Create Date: 2022-08-16 01:32:21.780478

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '74a2153dc53c'
down_revision = '60ea7a034f6e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('first_name', sa.String(), nullable=False, server_default='No name'))
    op.add_column('users', sa.Column('last_name', sa.String(), nullable=False, server_default='No name'))
    pass


def downgrade():
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')
    pass
