"""Add image_id foreign key to NFTs table for Image Service integration

Revision ID: 015_add_image_id_to_nfts
Revises: 014_add_image_table
Create Date: 2024-01-15 10:00:00.000000

This migration adds an optional image_id column to the nfts table to link
NFT records to Image records created by the ImageService. This enables:
- Proper image management and deduplication
- Separation of concerns (image storage vs NFT metadata)
- Support for updating images independently of NFT records
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '015_add_image_id_to_nfts'
down_revision = '014_add_image_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add image_id column to nfts table
    op.add_column('nfts', sa.Column(
        'image_id',
        postgresql.UUID(as_uuid=True),
        nullable=True
    ))
    
    # Create foreign key constraint (SET NULL on image deletion)
    op.create_foreign_key(
        'fk_nfts_image_id',
        'nfts', 'images',
        ['image_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for faster lookups by image_id
    op.create_index(
        'ix_nfts_image_id',
        'nfts',
        ['image_id']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_nfts_image_id', table_name='nfts')
    
    # Drop foreign key
    op.drop_constraint('fk_nfts_image_id', 'nfts', type_='foreignkey')
    
    # Drop column
    op.drop_column('nfts', 'image_id')
