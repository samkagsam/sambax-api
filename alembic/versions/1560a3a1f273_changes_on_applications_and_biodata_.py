"""changes on applications and biodata tables

Revision ID: 1560a3a1f273
Revises: 4234e3377b5f
Create Date: 2022-08-30 09:52:46.120783

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1560a3a1f273'
down_revision = '4234e3377b5f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('biodata', sa.Column('business_picture_url', sa.String(), nullable=True))
    op.add_column('applications', sa.Column('purpose_for_loan', sa.String(), nullable=False, server_default='None'))
    op.drop_column('applications', 'business_picture_url')

    pass


def downgrade() -> None:
    op.drop_column('biodata', 'business_picture_url')
    op.drop_column('applications', 'purpose_for_loan')
    op.add_column('applications', sa.Column('business_picture_url', sa.String(), nullable=True))

    pass
