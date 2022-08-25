"""add content column to posts table

Revision ID: 6b5649610344
Revises: f7a0b8b3c973
Create Date: 2022-08-12 22:45:40.777073

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b5649610344'
down_revision = 'f7a0b8b3c973'
branch_labels = None
depends_on = None


def upgrade():
    #content deleted by sam because of irrelevance
    pass


def downgrade():
    # content deleted by sam because of irrelevance

    pass
