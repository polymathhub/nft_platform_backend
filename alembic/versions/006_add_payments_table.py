"""Add payments table for deposits and withdrawals.

Revision ID: 006_add_payments_table
Revises: 005_normalize_userrole_enum
Create Date: 2026-02-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_payments_table'
down_revision = '005_normalize_userrole_enum'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create payments table for tracking deposits and withdrawals."""
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('payment_type', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, index=True),
        sa.Column('blockchain', sa.String(50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(20), nullable=False, server_default='USDT'),
        sa.Column('counterparty_address', sa.String(255), nullable=True),
        sa.Column('transaction_hash', sa.String(255), nullable=True, unique=True),
        sa.Column('transaction_hash_external', sa.String(255), nullable=True),
        sa.Column('network_fee', sa.Float(), nullable=True),
        sa.Column('platform_fee', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id']),
    )
    
    # Create indexes
    op.create_index('ix_payments_user_type_status', 'payments', ['user_id', 'payment_type', 'status'])
    op.create_index('ix_payments_wallet_type', 'payments', ['wallet_id', 'payment_type'])
    op.create_index('ix_payments_blockchain_hash', 'payments', ['blockchain', 'transaction_hash'])


def downgrade() -> None:
    """Drop payments table."""
    op.drop_index('ix_payments_blockchain_hash', 'payments')
    op.drop_index('ix_payments_wallet_type', 'payments')
    op.drop_index('ix_payments_user_type_status', 'payments')
    op.drop_table('payments')
