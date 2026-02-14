"""Initial schema - create base tables.

Revision ID: 000_initial_schema
Revises: None
Create Date: 2026-02-13 00:00:00.000000

This migration creates all base tables needed for the application:
- users
- wallets
- transactions
- listings
- offers
- orders
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '000_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all base tables."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('telegram_id', sa.String(50), nullable=True, unique=True),
        sa.Column('telegram_username', sa.String(100), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_verified', sa.Boolean(), default=False, nullable=False),
        sa.Column('user_role', sa.Enum('admin', 'user', name='userrole'), default='user', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    op.create_index('ix_users_user_role', 'users', ['user_role'])
    op.create_index('ix_users_username_active', 'users', ['username', 'is_active'])
    
    # Create wallets table
    op.create_table(
        'wallets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('blockchain', sa.String(50), nullable=False),
        sa.Column('wallet_type', sa.String(50), default='custodial', nullable=False),
        sa.Column('address', sa.String(255), nullable=False, unique=True),
        sa.Column('public_key', sa.String(500), nullable=True),
        sa.Column('encrypted_private_key', sa.String(1000), nullable=True),
        sa.Column('encrypted_mnemonic', sa.String(1000), nullable=True),
        sa.Column('is_primary', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('wallet_metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_wallets_user_id', 'wallets', ['user_id'])
    op.create_index('ix_wallets_user_blockchain', 'wallets', ['user_id', 'blockchain'])
    op.create_index('ix_wallets_address', 'wallets', ['address'])
    
    # Create nfts table
    op.create_table(
        'nfts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('global_nft_id', sa.String(255), nullable=False, unique=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('blockchain', sa.String(50), nullable=False),
        sa.Column('contract_address', sa.String(255), nullable=True),
        sa.Column('token_id', sa.String(255), nullable=True),
        sa.Column('mint_address', sa.String(255), nullable=True),
        sa.Column('owner_address', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), default='pending', nullable=False),
        sa.Column('is_locked', sa.Boolean(), default=False, nullable=False),
        sa.Column('lock_reason', sa.String(50), nullable=True),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('ipfs_hash', sa.String(255), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('attributes', postgresql.JSONB, nullable=True),
        sa.Column('rarity_score', sa.Float(), nullable=True),
        sa.Column('rarity_tier', sa.String(50), nullable=True),
        sa.Column('transaction_hash', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_nfts_user_id', 'nfts', ['user_id'])
    op.create_index('ix_nfts_wallet_id', 'nfts', ['wallet_id'])
    op.create_index('ix_nfts_name', 'nfts', ['name'])
    op.create_index('ix_nfts_status', 'nfts', ['status'])
    op.create_index('ix_nfts_token_id', 'nfts', ['token_id'])
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nft_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tx_hash', sa.String(255), nullable=True),
        sa.Column('tx_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='pending', nullable=False),
        sa.Column('blockchain', sa.String(50), nullable=False),
        sa.Column('from_address', sa.String(255), nullable=False),
        sa.Column('to_address', sa.String(255), nullable=False),
        sa.Column('amount', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('gas_fee', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['nft_id'], ['nfts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('ix_transactions_tx_hash', 'transactions', ['tx_hash'])
    op.create_index('ix_transactions_status', 'transactions', ['status'])
    
    # Create listings table
    op.create_table(
        'listings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('nft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_address', sa.String(255), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(50), nullable=False),
        sa.Column('blockchain', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='active', nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('listing_metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['nft_id'], ['nfts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_listings_nft_id', 'listings', ['nft_id'])
    op.create_index('ix_listings_seller_id', 'listings', ['seller_id'])
    op.create_index('ix_listings_status', 'listings', ['status'])
    op.create_index('ix_listings_blockchain', 'listings', ['blockchain'])
    
    # Create offers table
    op.create_table(
        'offers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('nft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('buyer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('offer_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='pending', nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('offer_metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['nft_id'], ['nfts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_offers_nft_id', 'offers', ['nft_id'])
    op.create_index('ix_offers_buyer_id', 'offers', ['buyer_id'])
    op.create_index('ix_offers_status', 'offers', ['status'])
    
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('offer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('buyer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('currency', sa.String(32), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('tx_hash', sa.String(256), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_orders_buyer_id', 'orders', ['buyer_id'])
    op.create_index('ix_orders_seller_id', 'orders', ['seller_id'])
    op.create_index('ix_orders_status', 'orders', ['status'])


def downgrade() -> None:
    """Drop all base tables."""
    # Drop in reverse order of dependencies
    op.drop_table('orders')
    op.drop_table('offers')
    op.drop_table('listings')
    op.drop_table('transactions')
    op.drop_table('nfts')
    op.drop_table('wallets')
    op.drop_table('users')
