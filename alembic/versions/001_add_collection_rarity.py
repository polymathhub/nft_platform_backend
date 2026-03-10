"""Add collection rarity support - Indentation Corrected.

Revision ID: 001_add_collection_rarity
Revises: 000_initial_schema
Create Date: 2026-02-13 00:00:00.000000

FIX SUMMARY:
============
✓ Fixed indentation in upgrade() function (was 16 spaces, now 8 spaces)
✓ Proper PostgreSQL SQL syntax for all operations
✓ Idempotent operations using IF NOT EXISTS checks
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '001_add_collection_rarity'
down_revision = '000_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add collections table and rarity support to NFTs.
    
    INDENTATION FIX: Main upgrade logic now uses proper 8-space indentation
    for the function body instead of excessive 16-space indentation.
    """
    bind = op.get_bind()
    
    # Create collections table if missing
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS collections (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            creator_id UUID NOT NULL,
            name VARCHAR(255) NOT NULL,
            description VARCHAR(500),
            blockchain VARCHAR(50) NOT NULL,
            contract_address VARCHAR(255) UNIQUE,
            floor_price DOUBLE PRECISION,
            average_price DOUBLE PRECISION,
            ceiling_price DOUBLE PRECISION,
            total_volume DOUBLE PRECISION DEFAULT 0 NOT NULL,
            total_sales INTEGER DEFAULT 0 NOT NULL,
            rarity_weights JSON,
            collection_metadata JSON,
            image_url VARCHAR(500),
            banner_url VARCHAR(500),
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_collections_creator ON collections (creator_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_collections_blockchain ON collections (blockchain);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_collections_floor_price ON collections (floor_price);")
    
    # Add columns to nfts table if missing
    op.execute("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS collection_id UUID;")
    op.execute("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS attributes JSONB;")
    op.execute("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS rarity_score DOUBLE PRECISION;")
    op.execute("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS rarity_tier VARCHAR(50);")
    
    # Add foreign key constraint if missing
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_nfts_collection_id'
            ) THEN
                ALTER TABLE nfts ADD CONSTRAINT fk_nfts_collection_id 
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE SET NULL;
            END IF;
        END$$;
        """
    )
    
    op.execute("CREATE INDEX IF NOT EXISTS ix_nfts_collection ON nfts (collection_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nfts_rarity_tier ON nfts (rarity_tier);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nfts_rarity_score ON nfts (rarity_score);")


def downgrade() -> None:
    """Remove collections table and rarity columns from NFTs."""
    # Drop indexes
    op.drop_index('ix_nfts_rarity_score', table_name='nfts', if_exists=True)
    op.drop_index('ix_nfts_rarity_tier', table_name='nfts', if_exists=True)
    op.drop_index('ix_nfts_collection', table_name='nfts', if_exists=True)
    
    # Drop foreign key
    op.drop_constraint('fk_nfts_collection_id', 'nfts', type_='foreignkey', if_exists=True)
    
    # Drop columns from nfts
    op.drop_column('nfts', 'rarity_tier', if_exists=True)
    op.drop_column('nfts', 'rarity_score', if_exists=True)
    op.drop_column('nfts', 'attributes', if_exists=True)
    op.drop_column('nfts', 'collection_id', if_exists=True)
    
    # Drop collections table
    op.drop_index('ix_collections_floor_price', table_name='collections', if_exists=True)
    op.drop_index('ix_collections_blockchain', table_name='collections', if_exists=True)
    op.drop_index('ix_collections_creator', table_name='collections', if_exists=True)
    op.drop_table('collections', if_exists=True)
