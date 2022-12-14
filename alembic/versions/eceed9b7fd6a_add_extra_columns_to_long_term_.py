"""Add extra columns to long term transactions table

Revision ID: eceed9b7fd6a
Revises: 9bdc4ff1b87d
Create Date: 2023-01-05 07:56:13.864666

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eceed9b7fd6a'
down_revision = '9bdc4ff1b87d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('long_term_group_transactions', sa.Column('old_balance', sa.Integer(), server_default='0', nullable=False))
    op.add_column('long_term_group_transactions', sa.Column('new_balance', sa.Integer(), server_default='0', nullable=False))
    op.add_column('long_term_group_transactions', sa.Column('made_by', sa.String(), server_default='self', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('long_term_group_transactions', 'made_by')
    op.drop_column('long_term_group_transactions', 'new_balance')
    op.drop_column('long_term_group_transactions', 'old_balance')
    # ### end Alembic commands ###
