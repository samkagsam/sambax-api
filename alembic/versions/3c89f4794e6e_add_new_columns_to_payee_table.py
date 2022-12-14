"""Add new columns to payee table

Revision ID: 3c89f4794e6e
Revises: a39b32949928
Create Date: 2022-11-25 04:55:29.721394

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c89f4794e6e'
down_revision = 'a39b32949928'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('payees', sa.Column('approval_status', sa.String(), server_default='None', nullable=False))
    op.add_column('payees', sa.Column('approval_count', sa.Integer(), server_default='0', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('payees', 'approval_count')
    op.drop_column('payees', 'approval_status')
    # ### end Alembic commands ###
