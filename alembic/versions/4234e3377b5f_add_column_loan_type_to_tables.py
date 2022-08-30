"""add column loan_type to tables

Revision ID: 4234e3377b5f
Revises: 6fe61e26b779
Create Date: 2022-08-30 08:46:55.441824

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4234e3377b5f'
down_revision = '6fe61e26b779'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('loans', sa.Column('loan_type', sa.String(), nullable=False, server_default='Business'))
    pass


def downgrade() -> None:
    op.drop_column('loans', 'loan_type')
    pass
