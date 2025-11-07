"""Create statement_log table

Revision ID: 0001_create_statement_log
Revises: 
Create Date: 2025-11-06 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_statement_log'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'statement_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('company_id', sa.Integer, sa.ForeignKey('company.id', ondelete='CASCADE')),
        sa.Column('bank_code', sa.String(), nullable=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('accountno', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('opening_balance', sa.String(), nullable=True),
        sa.Column('closing_balance', sa.String(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('mt940_filename', sa.String(), nullable=True),
        sa.Column('processed_at', sa.TIMESTAMP(), server_default=sa.text('now()')),
    )
    op.create_index('idx_statement_log_company_id', 'statement_log', ['company_id'])
    op.create_index('idx_statement_log_user_id', 'statement_log', ['user_id'])
    op.create_index('idx_statement_log_bank_code', 'statement_log', ['bank_code'])


def downgrade():
    op.drop_index('idx_statement_log_bank_code', table_name='statement_log')
    op.drop_index('idx_statement_log_user_id', table_name='statement_log')
    op.drop_index('idx_statement_log_company_id', table_name='statement_log')
    op.drop_table('statement_log')
