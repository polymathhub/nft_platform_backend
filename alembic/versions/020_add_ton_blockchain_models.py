"""Add TON wallet sessions and blockchain transactions models

Revision ID: 020_ton_blockchain_models
Revises: 019_fix_userrole_enum_case
Create Date: 2026-04-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import ProgrammingError

# revision identifiers, used by Alembic.
revision = '020_ton_blockchain_models'
down_revision = '019_fix_userrole_enum_case'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create BlockchainTransactionStatus enum type with raw SQL for proper IF NOT EXISTS handling
    # PostgreSQL doesn't support IF NOT EXISTS for CREATE TYPE, so we use DO...EXCEPTION handling
    connection = op.get_bind()
    try:
        connection.execute(
            sa.text("""
            DO $$ BEGIN
                CREATE TYPE blockchaintransactionstatus AS ENUM ('pending', 'in_progress', 'confirmed', 'failed');
            EXCEPTION WHEN duplicate_object THEN
                -- Type already exists, continue silently
                NULL;
            END $$;
            """)
        )
    except Exception as e:
        # If any error occurs, log it but continue (enum might already exist)
        print(f"Note: Enum creation message: {e}")
        pass
    
    # Create ton_wallet_sessions table (skip if already exists)
    try:
        op.create_table(
            'ton_wallet_sessions',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('ton_wallet_id', sa.UUID(), nullable=True),
            sa.Column('public_key', sa.String(256), nullable=True),
            sa.Column('session_hash', sa.String(128), nullable=True),
            sa.Column('device_platform', sa.String(50), nullable=True),
            sa.Column('device_name', sa.String(255), nullable=True),
            sa.Column('app_name', sa.String(100), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('transaction_count', sa.Integer(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['ton_wallet_id'], ['ton_wallets.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_ton_wallet_sessions_user_id', 'ton_wallet_sessions', ['user_id'], unique=False)
        op.create_index('ix_ton_wallet_sessions_ton_wallet_id', 'ton_wallet_sessions', ['ton_wallet_id'], unique=False)
        op.create_index('ix_ton_wallet_sessions_is_active', 'ton_wallet_sessions', ['is_active'], unique=False)
        op.create_index('ix_ton_wallet_sessions_public_key', 'ton_wallet_sessions', ['public_key'], unique=False)
        op.create_index('ix_ton_wallet_sessions_session_hash', 'ton_wallet_sessions', ['session_hash'], unique=False)
        op.create_index('ix_ton_wallet_sessions_device', 'ton_wallet_sessions', ['device_platform', 'device_name'], unique=False)
        op.create_index('ix_ton_wallet_sessions_user', 'ton_wallet_sessions', ['user_id', 'is_active'], unique=False)
        op.create_index('ix_ton_wallet_sessions_wallet', 'ton_wallet_sessions', ['ton_wallet_id', 'is_active'], unique=False)
    except ProgrammingError as e:
        if 'already exists' not in str(e).lower():
            raise
        print("ton_wallet_sessions table already exists, skipping creation")


    # Create blockchain_transactions table (skip if already exists)
    try:
        op.create_table(
            'blockchain_transactions',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('transaction_hash', sa.String(256), nullable=False),
            sa.Column('wallet_address', sa.String(256), nullable=False),
            sa.Column('from_address', sa.String(256), nullable=True),
            sa.Column('contract_address', sa.String(256), nullable=True),
            sa.Column('payload_boc', sa.Text(), nullable=True),
            sa.Column('tx_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('confirmations', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('trust_level', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'confirmed', 'failed', name='blockchaintransactionstatus', create_type=False), nullable=False, server_default='pending'),
            sa.Column('related_nft_id', sa.UUID(), nullable=True),
            sa.Column('verification_attempts', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('next_verification_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['related_nft_id'], ['nfts.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_blockchain_transactions_user_id', 'blockchain_transactions', ['user_id'], unique=False)
        op.create_index('ix_blockchain_transactions_transaction_hash', 'blockchain_transactions', ['transaction_hash'], unique=False)
        op.create_index('ix_blockchain_transactions_wallet_address', 'blockchain_transactions', ['wallet_address'], unique=False)
        op.create_index('ix_blockchain_transactions_from_address', 'blockchain_transactions', ['from_address'], unique=False)
        op.create_index('ix_blockchain_transactions_contract_address', 'blockchain_transactions', ['contract_address'], unique=False)
        op.create_index('ix_blockchain_transactions_status', 'blockchain_transactions', ['status'], unique=False)
        op.create_index('ix_blockchain_transactions_related_nft_id', 'blockchain_transactions', ['related_nft_id'], unique=False)
        op.create_index('ix_blockchain_tx_user', 'blockchain_transactions', ['user_id', 'created_at'], unique=False)
        op.create_index('ix_blockchain_tx_hash', 'blockchain_transactions', ['transaction_hash'], unique=False)
        op.create_index('ix_blockchain_tx_wallet', 'blockchain_transactions', ['wallet_address', 'status'], unique=False)
        op.create_index('ix_blockchain_tx_contract', 'blockchain_transactions', ['contract_address'], unique=False)
        op.create_index('ix_blockchain_tx_nft', 'blockchain_transactions', ['related_nft_id'], unique=False)
    except ProgrammingError as e:
        if 'already exists' not in str(e).lower():
            raise
        print("blockchain_transactions table already exists, skipping creation")



def downgrade() -> None:
    op.drop_index('ix_blockchain_tx_nft', table_name='blockchain_transactions')
    op.drop_index('ix_blockchain_tx_contract', table_name='blockchain_transactions')
    op.drop_index('ix_blockchain_tx_wallet', table_name='blockchain_transactions')
    op.drop_index('ix_blockchain_tx_hash', table_name='blockchain_transactions')
    op.drop_index('ix_blockchain_tx_user', table_name='blockchain_transactions')
    op.drop_index('ix_blockchain_transactions_related_nft_id', table_name='blockchain_transactions')
    op.drop_index('ix_blockchain_transactions_status', table_name='blockchain_transactions')
    op.drop_index('ix_blockchain_transactions_contract_address', table_name='blockchain_transactions')
    op.drop_index('ix_blockchain_transactions_from_address', table_name='blockchain_transactions')
    op.drop_index('ix_blockchain_transactions_wallet_address', table_name='blockchain_transactions')
    op.drop_index('ix_blockchain_transactions_transaction_hash', table_name='blockchain_transactions')
    op.drop_index('ix_blockchain_transactions_user_id', table_name='blockchain_transactions')
    op.drop_table('blockchain_transactions')

    op.drop_index('ix_ton_wallet_sessions_wallet', table_name='ton_wallet_sessions')
    op.drop_index('ix_ton_wallet_sessions_user', table_name='ton_wallet_sessions')
    op.drop_index('ix_ton_wallet_sessions_device', table_name='ton_wallet_sessions')
    op.drop_index('ix_ton_wallet_sessions_session_hash', table_name='ton_wallet_sessions')
    op.drop_index('ix_ton_wallet_sessions_public_key', table_name='ton_wallet_sessions')
    op.drop_index('ix_ton_wallet_sessions_is_active', table_name='ton_wallet_sessions')
    op.drop_index('ix_ton_wallet_sessions_ton_wallet_id', table_name='ton_wallet_sessions')
    op.drop_index('ix_ton_wallet_sessions_user_id', table_name='ton_wallet_sessions')
    op.drop_table('ton_wallet_sessions')

    blockchain_status_enum = postgresql.ENUM('pending', 'in_progress', 'confirmed', 'failed', name='blockchaintransactionstatus')
    blockchain_status_enum.drop(op.get_bind(), checkfirst=True)
