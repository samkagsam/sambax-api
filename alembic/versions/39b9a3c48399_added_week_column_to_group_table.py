"""Added week column to group table

Revision ID: 39b9a3c48399
Revises: 3c89f4794e6e
Create Date: 2022-11-25 23:08:44.139121

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '39b9a3c48399'
down_revision = '3c89f4794e6e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('groups', sa.Column('week', sa.Integer(), server_default='0', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('groups', 'week')
    # ### end Alembic commands ###
