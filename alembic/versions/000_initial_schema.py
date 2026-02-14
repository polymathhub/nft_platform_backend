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
        # Use idempotent DDL so running migrations against an existing schema is safe
        bind = op.get_bind()

        # Ensure enum types exist
        bind.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                        CREATE TYPE userrole AS ENUM ('admin','user');
                    END IF;
                END$$;
                """
        )

        # Create users table if missing
        bind.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    telegram_id VARCHAR(50) UNIQUE,
                    telegram_username VARCHAR(100),
                    full_name VARCHAR(255),
                    avatar_url VARCHAR(500),
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    is_verified BOOLEAN NOT NULL DEFAULT false,
                    user_role userrole NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
                    last_login TIMESTAMP WITHOUT TIME ZONE
                );
                """
        )
        bind.execute("CREATE INDEX IF NOT EXISTS ix_users_is_active ON users (is_active);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_users_user_role ON users (user_role);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_users_username_active ON users (username, is_active);")

        # Create wallets table if missing
        bind.execute(
                """
                CREATE TABLE IF NOT EXISTS wallets (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL,
                    blockchain VARCHAR(50) NOT NULL,
                    wallet_type VARCHAR(50) NOT NULL DEFAULT 'custodial',
                    address VARCHAR(255) UNIQUE NOT NULL,
                    public_key VARCHAR(500),
                    encrypted_private_key VARCHAR(1000),
                    encrypted_mnemonic VARCHAR(1000),
                    is_primary BOOLEAN NOT NULL DEFAULT false,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    wallet_metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
                );
                """
        )
        bind.execute("CREATE INDEX IF NOT EXISTS ix_wallets_user_id ON wallets (user_id);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_wallets_user_blockchain ON wallets (user_id, blockchain);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_wallets_address ON wallets (address);")

        # Create nfts table if missing
        bind.execute(
                """
                CREATE TABLE IF NOT EXISTS nfts (
                    id UUID PRIMARY KEY,
                    global_nft_id VARCHAR(255) UNIQUE NOT NULL,
                    user_id UUID NOT NULL,
                    wallet_id UUID NOT NULL,
                    collection_id UUID,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    blockchain VARCHAR(50) NOT NULL,
                    contract_address VARCHAR(255),
                    token_id VARCHAR(255),
                    mint_address VARCHAR(255),
                    owner_address VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    is_locked BOOLEAN NOT NULL DEFAULT false,
                    lock_reason VARCHAR(50),
                    locked_until TIMESTAMP WITHOUT TIME ZONE,
                    ipfs_hash VARCHAR(255),
                    image_url VARCHAR(500),
                    attributes JSONB,
                    rarity_score FLOAT,
                    rarity_tier VARCHAR(50),
                    transaction_hash VARCHAR(255),
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
                );
                """
        )
        bind.execute("CREATE INDEX IF NOT EXISTS ix_nfts_user_id ON nfts (user_id);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_nfts_wallet_id ON nfts (wallet_id);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_nfts_name ON nfts (name);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_nfts_status ON nfts (status);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_nfts_token_id ON nfts (token_id);")

        # Create transactions table if missing
        bind.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL,
                    nft_id UUID,
                    wallet_id UUID NOT NULL,
                    tx_hash VARCHAR(255),
                    tx_type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    blockchain VARCHAR(50) NOT NULL,
                    from_address VARCHAR(255) NOT NULL,
                    to_address VARCHAR(255) NOT NULL,
                    amount NUMERIC(20,8),
                    gas_fee NUMERIC(20,8),
                    error_message TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
                );
                """
        )
        bind.execute("CREATE INDEX IF NOT EXISTS ix_transactions_user_id ON transactions (user_id);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_transactions_tx_hash ON transactions (tx_hash);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_transactions_status ON transactions (status);")

        # Create listings table if missing
        bind.execute(
                """
                CREATE TABLE IF NOT EXISTS listings (
                    id UUID PRIMARY KEY,
                    nft_id UUID NOT NULL,
                    seller_id UUID NOT NULL,
                    seller_address VARCHAR(255) NOT NULL,
                    price DOUBLE PRECISION NOT NULL,
                    currency VARCHAR(50) NOT NULL,
                    blockchain VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    expires_at TIMESTAMP WITHOUT TIME ZONE,
                    listing_metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
                );
                """
        )
        bind.execute("CREATE INDEX IF NOT EXISTS ix_listings_nft_id ON listings (nft_id);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_listings_seller_id ON listings (seller_id);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_listings_status ON listings (status);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_listings_blockchain ON listings (blockchain);")

        # Create offers table if missing
        bind.execute(
                """
                CREATE TABLE IF NOT EXISTS offers (
                    id UUID PRIMARY KEY,
                    nft_id UUID NOT NULL,
                    buyer_id UUID NOT NULL,
                    seller_id UUID NOT NULL,
                    offer_amount DOUBLE PRECISION NOT NULL,
                    currency VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    expires_at TIMESTAMP WITHOUT TIME ZONE,
                    offer_metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
                );
                """
        )
        bind.execute("CREATE INDEX IF NOT EXISTS ix_offers_nft_id ON offers (nft_id);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_offers_buyer_id ON offers (buyer_id);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_offers_status ON offers (status);")

        # Create orders table if missing
        bind.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id UUID PRIMARY KEY,
                    listing_id UUID,
                    offer_id UUID,
                    buyer_id UUID NOT NULL,
                    seller_id UUID NOT NULL,
                    amount NUMERIC(18,6) NOT NULL,
                    currency VARCHAR(32) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    tx_hash VARCHAR(256),
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
                );
                """
        )
        bind.execute("CREATE INDEX IF NOT EXISTS ix_orders_buyer_id ON orders (buyer_id);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_orders_seller_id ON orders (seller_id);")
        bind.execute("CREATE INDEX IF NOT EXISTS ix_orders_status ON orders (status);")


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
