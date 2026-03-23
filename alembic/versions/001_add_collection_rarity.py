from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision = '001_add_collection_rarity'
down_revision = '000_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create collections table if missing
    op.execute(sa.text("""
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
        )
    """))
    
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_collections_creator ON collections (creator_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_collections_blockchain ON collections (blockchain)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_collections_floor_price ON collections (floor_price)"))

    # Add columns to nfts table if missing
    op.execute(sa.text("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS collection_id UUID"))
    op.execute(sa.text("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS attributes JSONB"))
    op.execute(sa.text("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS rarity_score DOUBLE PRECISION"))
    op.execute(sa.text("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS rarity_tier VARCHAR(50)"))

    # Add foreign key constraint if missing
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_nfts_collection_id'
            ) THEN
                ALTER TABLE nfts ADD CONSTRAINT fk_nfts_collection_id 
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE SET NULL;
            END IF;
        END$$
    """))

    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_nfts_collection ON nfts (collection_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_nfts_rarity_tier ON nfts (rarity_tier)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_nfts_rarity_score ON nfts (rarity_score)"))


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_nfts_rarity_score', 'nfts')
    op.drop_index('ix_nfts_rarity_tier', 'nfts')
    op.drop_index('ix_nfts_collection', 'nfts')
    
    # Drop foreign key
    op.drop_constraint('fk_nfts_collection_id', 'nfts', type_='foreignkey')
    
    # Drop columns from nfts
    op.drop_column('nfts', 'rarity_tier')
    op.drop_column('nfts', 'rarity_score')
    op.drop_column('nfts', 'attributes')
    op.drop_column('nfts', 'collection_id')
    
    # Drop collections table
    op.drop_index('ix_collections_floor_price', 'collections')
    op.drop_index('ix_collections_blockchain', 'collections')
    op.drop_index('ix_collections_creator', 'collections')
    op.drop_table('collections')
