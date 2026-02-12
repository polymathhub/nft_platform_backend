
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision = '001_add_collection_rarity'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create collections table
    op.create_table(
        'collections',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('creator_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('blockchain', sa.String(50), nullable=False),
        sa.Column('contract_address', sa.String(255), nullable=True, unique=True),
        sa.Column('floor_price', sa.Float(), nullable=True),
        sa.Column('average_price', sa.Float(), nullable=True),
        sa.Column('ceiling_price', sa.Float(), nullable=True),
        sa.Column('total_volume', sa.Float(), default=0, nullable=False),
        sa.Column('total_sales', sa.Integer(), default=0, nullable=False),
        sa.Column('rarity_weights', sa.JSON(), nullable=True),
        sa.Column('collection_metadata', sa.JSON(), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('banner_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
    )
    op.create_index('ix_collections_creator', 'collections', ['creator_id'])
    op.create_index('ix_collections_blockchain', 'collections', ['blockchain'])
    op.create_index('ix_collections_floor_price', 'collections', ['floor_price'])
    
    # Add columns to nfts table
    op.add_column('nfts', sa.Column('collection_id', sa.String(36), nullable=True))
    op.add_column('nfts', sa.Column('attributes', sa.JSON(), nullable=True))
    op.add_column('nfts', sa.Column('rarity_score', sa.Float(), nullable=True))
    op.add_column('nfts', sa.Column('rarity_tier', sa.String(50), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_nfts_collection_id',
        'nfts',
        'collections',
        ['collection_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Add indexes
    op.create_index('ix_nfts_collection', 'nfts', ['collection_id'])
    op.create_index('ix_nfts_rarity_tier', 'nfts', ['rarity_tier'])
    op.create_index('ix_nfts_rarity_score', 'nfts', ['rarity_score'])


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
