"""add last few columns to posts table

Revision ID: 371244eae8bf
Revises: 8c7460c4afbb
Create Date: 2022-08-13 05:31:11.485497

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '371244eae8bf'
down_revision = '8c7460c4afbb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('posts', sa.Column('published', sa.Boolean(), nullable=False, server_default='True'))
    op.add_column('posts', sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))
    pass


def downgrade():
    op.drop_column("posts", "published")
    op.drop_column("posts", "created_at")
    pass
