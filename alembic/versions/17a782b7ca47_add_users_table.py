"""add users table

Revision ID: 17a782b7ca47
Revises: 6b5649610344
Create Date: 2022-08-12 23:09:56.463922

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17a782b7ca47'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users", sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
                    sa.Column('phone_number', sa.Integer(), nullable=False),
                    sa.Column('password', sa.String(), nullable=False),
                    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('phone_number')
                    )
    pass


def downgrade():
    op.drop_table('users')
    pass
