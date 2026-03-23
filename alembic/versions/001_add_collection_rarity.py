from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_add_collection_rarity'
down_revision = '000_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add rarity tier to NFTs table if it doesn't exist
    op.execute("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS rarity_tier VARCHAR(50);")
    op.execute("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS rarity_score DOUBLE PRECISION;")
    
    # Add attributes to NFTs table
    op.execute("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS attributes JSONB DEFAULT '{}';")
    
    # Create indexes on nfts table
    op.execute("CREATE INDEX IF NOT EXISTS ix_nfts_collection ON nfts (collection_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nfts_rarity_tier ON nfts (rarity_tier);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nfts_rarity_score ON nfts (rarity_score);")

def downgrade() -> None:
    op.drop_index('ix_nfts_rarity_score', table_name='nfts', if_exists=True)
    op.drop_index('ix_nfts_rarity_tier', table_name='nfts', if_exists=True)
    op.drop_index('ix_nfts_collection', table_name='nfts', if_exists=True)
    op.drop_column('nfts', 'attributes', if_exists=True)
    op.drop_column('nfts', 'rarity_score', if_exists=True)
    op.drop_column('nfts', 'rarity_tier', if_exists=True)
