"""Add Image table for NFT media storage

Revision ID: 014_add_image_table
Revises: 013_add_wallet_address_to_users
Create Date: 2024-01-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_add_image_table'
down_revision = '013_add_wallet_address_to_users'
branch_labels = None
depends_on = None


def upgrade():
    """Create images table for storing NFT media files"""
    
    # Create ENUM for ImageType
    image_type_enum = sa.Enum(
        'nft_preview',
        'nft_full',
        'collection_cover',
        'user_avatar',
        'marketplace_thumb',
        name='imagetype',
        native_enum=False
    )
    image_type_enum.create(op.get_bind(), checkfirst=True)

    # Create images table
    op.create_table(
        'images',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('uploaded_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nft_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=True),
        sa.Column('mime_type', sa.String(50), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=False),
        sa.Column('width', sa.Integer, nullable=True),
        sa.Column('height', sa.Integer, nullable=True),
        sa.Column('image_type', image_type_enum, nullable=False, server_default='nft_preview'),
        sa.Column('storage_type', sa.String(50), nullable=False, server_default='database'),
        sa.Column('storage_path', sa.String(500), nullable=True),
        sa.Column('md5_hash', sa.String(32), nullable=True, unique=True),
        sa.Column('sha256_hash', sa.String(64), nullable=True, unique=True),
        sa.Column('is_public', sa.String(50), nullable=False, server_default='private'),
        sa.Column('access_token', sa.String(64), nullable=True, unique=True),
        sa.Column('base64_data', sa.String(2097152), nullable=True),
        sa.Column('base64_thumbnail', sa.String(100000), nullable=True),
        sa.Column('uploaded_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('last_accessed', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['nft_id'], ['nfts.id'], ondelete='SET NULL'),
    )

    # Create indexes
    op.create_index('ix_images_user_type', 'images', ['uploaded_by_user_id', 'image_type'])
    op.create_index('ix_images_nft', 'images', ['nft_id'])
    op.create_index('ix_images_public', 'images', ['is_public'])
    op.create_index('ix_images_md5_hash', 'images', ['md5_hash'])
    op.create_index('ix_images_sha256_hash', 'images', ['sha256_hash'])
    op.create_index('ix_images_access_token', 'images', ['access_token'])

    # Extend NFT.image_url field from VARCHAR(500) to VARCHAR(2083)
    op.alter_column(
        'nfts',
        'image_url',
        existing_type=sa.String(500),
        type_=sa.String(2083),
        nullable=True
    )


def downgrade():
    """Remove images table"""
    
    # Revert NFT.image_url field size
    op.alter_column(
        'nfts',
        'image_url',
        existing_type=sa.String(2083),
        type_=sa.String(500),
        nullable=True
    )

    # Drop indexes
    op.drop_index('ix_images_access_token', 'images')
    op.drop_index('ix_images_sha256_hash', 'images')
    op.drop_index('ix_images_md5_hash', 'images')
    op.drop_index('ix_images_public', 'images')
    op.drop_index('ix_images_nft', 'images')
    op.drop_index('ix_images_user_type', 'images')

    # Drop table
    op.drop_table('images')

    # Drop ENUM
    image_type_enum = sa.Enum(
        'nft_preview',
        'nft_full',
        'collection_cover',
        'user_avatar',
        'marketplace_thumb',
        name='imagetype',
        native_enum=False
    )
    image_type_enum.drop(op.get_bind(), checkfirst=True)
