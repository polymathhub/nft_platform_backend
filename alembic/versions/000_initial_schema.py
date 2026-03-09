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
    # Use SQLAlchemy table creation for portability across dialects
    # Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(length=255), unique=True, nullable=False),
        sa.Column('username', sa.String(length=100), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('telegram_id', sa.String(length=50), unique=True, nullable=True),
        sa.Column('telegram_username', sa.String(length=100), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('user_role', sa.String(length=32), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_is_active', 'users', ['is_active'], unique=False)
    op.create_index('ix_users_username_active', 'users', ['username', 'is_active'], unique=False)

    # Wallets
    op.create_table(
        'wallets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('blockchain', sa.String(length=50), nullable=False),
        sa.Column('wallet_type', sa.String(length=50), nullable=False, server_default='custodial'),
        sa.Column('address', sa.String(length=255), unique=True, nullable=False),
        sa.Column('public_key', sa.String(length=500), nullable=True),
        sa.Column('encrypted_private_key', sa.String(length=1000), nullable=True),
        sa.Column('encrypted_mnemonic', sa.String(length=1000), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.Column('wallet_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_wallets_user_id', 'wallets', ['user_id'], unique=False)
    op.create_index('ix_wallets_user_blockchain', 'wallets', ['user_id', 'blockchain'], unique=False)
    op.create_index('ix_wallets_address', 'wallets', ['address'], unique=False)

    # NFTs
    op.create_table(
        'nfts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('global_nft_id', sa.String(length=255), unique=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('blockchain', sa.String(length=50), nullable=False),
        sa.Column('contract_address', sa.String(length=255), nullable=True),
        sa.Column('token_id', sa.String(length=255), nullable=True),
        sa.Column('mint_address', sa.String(length=255), nullable=True),
        sa.Column('owner_address', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('lock_reason', sa.String(length=50), nullable=True),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('ipfs_hash', sa.String(length=255), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('attributes', sa.JSON(), nullable=True),
        sa.Column('rarity_score', sa.Float(), nullable=True),
        sa.Column('rarity_tier', sa.String(length=50), nullable=True),
        sa.Column('transaction_hash', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_nfts_user_id', 'nfts', ['user_id'], unique=False)
    op.create_index('ix_nfts_wallet_id', 'nfts', ['wallet_id'], unique=False)
    op.create_index('ix_nfts_name', 'nfts', ['name'], unique=False)
    op.create_index('ix_nfts_status', 'nfts', ['status'], unique=False)
    op.create_index('ix_nfts_token_id', 'nfts', ['token_id'], unique=False)

    # Transactions
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nft_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tx_hash', sa.String(length=255), nullable=True),
        sa.Column('tx_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('blockchain', sa.String(length=50), nullable=False),
        sa.Column('from_address', sa.String(length=255), nullable=False),
        sa.Column('to_address', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(20, 8), nullable=True),
        sa.Column('gas_fee', sa.Numeric(20, 8), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('transaction_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'], unique=False)
    op.create_index('ix_transactions_tx_hash', 'transactions', ['tx_hash'], unique=False)
    op.create_index('ix_transactions_status', 'transactions', ['status'], unique=False)

    # Listings
    op.create_table(
        'listings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_address', sa.String(length=255), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=50), nullable=False),
        sa.Column('blockchain', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('listing_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_listings_nft_id', 'listings', ['nft_id'], unique=False)
    op.create_index('ix_listings_seller_id', 'listings', ['seller_id'], unique=False)
    op.create_index('ix_listings_status', 'listings', ['status'], unique=False)
    op.create_index('ix_listings_blockchain', 'listings', ['blockchain'], unique=False)

    # Offers
    op.create_table(
        'offers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('buyer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('offer_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('offer_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_offers_nft_id', 'offers', ['nft_id'], unique=False)
    op.create_index('ix_offers_buyer_id', 'offers', ['buyer_id'], unique=False)
    op.create_index('ix_offers_status', 'offers', ['status'], unique=False)

    # Orders
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('offer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('buyer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(18, 6), nullable=False),
        sa.Column('currency', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('tx_hash', sa.String(length=256), nullable=True),
        sa.Column('order_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_orders_buyer_id', 'orders', ['buyer_id'], unique=False)
    op.create_index('ix_orders_seller_id', 'orders', ['seller_id'], unique=False)
    op.create_index('ix_orders_status', 'orders', ['status'], unique=False)


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
