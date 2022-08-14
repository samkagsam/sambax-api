"""add foreign key to posts table

Revision ID: 8c7460c4afbb
Revises: 17a782b7ca47
Create Date: 2022-08-12 23:53:34.708085

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c7460c4afbb'
down_revision = '17a782b7ca47'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('posts', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_foreign_key('posts_users_fk', source_table="posts", referent_table="users", local_cols=["user_id"],
                          remote_cols=["id"], ondelete="CASCADE")
    pass


def downgrade():
    op.drop_column("posts", "user_id")
    op.drop_constraint("posts_users_fk", table_name="posts")
    pass
