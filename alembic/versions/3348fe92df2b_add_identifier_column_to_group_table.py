"""Add identifier column to group table

Revision ID: 3348fe92df2b
Revises: 0b1a2d868902
Create Date: 2022-12-17 08:08:57.592931

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3348fe92df2b'
down_revision = '0b1a2d868902'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('groups', sa.Column('identifier', sa.String(), server_default='None', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('groups', 'identifier')
    # ### end Alembic commands ###
