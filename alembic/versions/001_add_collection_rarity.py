from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = '001_add_collection_rarity'
down_revision = '000_initial_schema'
branch_labels = None
depends_on = None
def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE INDEX IF NOT EXISTS ix_collections_creator ON collections (creator_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_collections_blockchain ON collections (blockchain);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_collections_floor_price ON collections (floor_price);")
    op.execute("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS collection_id UUID;")
    op.execute("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS attributes JSONB;")
    op.execute("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS rarity_score DOUBLE PRECISION;")
    op.execute("ALTER TABLE nfts ADD COLUMN IF NOT EXISTS rarity_tier VARCHAR(50);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nfts_collection ON nfts (collection_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nfts_rarity_tier ON nfts (rarity_tier);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nfts_rarity_score ON nfts (rarity_score);")
def downgrade() -> None:
    op.drop_index('ix_nfts_rarity_score', table_name='nfts', if_exists=True)
    op.drop_index('ix_nfts_rarity_tier', table_name='nfts', if_exists=True)
    op.drop_index('ix_nfts_collection', table_name='nfts', if_exists=True)
    op.drop_constraint('fk_nfts_collection_id', 'nfts', type_='foreignkey', if_exists=True)
    op.drop_column('nfts', 'rarity_tier', if_exists=True)
    op.drop_column('nfts', 'rarity_score', if_exists=True)
    op.drop_column('nfts', 'attributes', if_exists=True)
    op.drop_column('nfts', 'collection_id', if_exists=True)
    op.drop_index('ix_collections_floor_price', table_name='collections', if_exists=True)
    op.drop_index('ix_collections_blockchain', table_name='collections', if_exists=True)
    op.drop_index('ix_collections_creator', table_name='collections', if_exists=True)
    op.drop_table('collections', if_exists=True)
