"""Add Long Term Groups

Revision ID: b7d468643c06
Revises: 3348fe92df2b
Create Date: 2023-01-02 15:14:40.036634

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7d468643c06'
down_revision = '3348fe92df2b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('long_term_group_members',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), server_default='0', nullable=False),
    sa.Column('user_id', sa.Integer(), server_default='0', nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('approval_status', sa.String(), server_default='None', nullable=False),
    sa.Column('approval_count', sa.Integer(), server_default='0', nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('long_term_groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('account_balance', sa.Integer(), server_default='0', nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('payout_date', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('group_admin', sa.Integer(), server_default='0', nullable=False),
    sa.Column('cycle', sa.Integer(), server_default='0', nullable=False),
    sa.Column('identifier', sa.String(), server_default='None', nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('long_term_group_transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('cycle', sa.String(), server_default='None', nullable=False),
    sa.Column('transaction_type', sa.String(), server_default='None', nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('long_term_group_transactions')
    op.drop_table('long_term_groups')
    op.drop_table('long_term_group_members')
    # ### end Alembic commands ###
