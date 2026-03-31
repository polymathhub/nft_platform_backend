"""Add creator profile columns to users table

Revision ID: 016_add_creator_columns
Revises: 015_add_image_id_to_nfts
Create Date: 2026-03-31 03:30:00.000000

This migration adds creator profile columns to the users table:
- is_creator: Boolean flag indicating if user is a creator
- creator_name: Display name for creator profile
- creator_bio: Bio/description for creator profile
- creator_avatar_url: Avatar URL for creator profile
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '016_add_creator_columns'
down_revision = '015_add_image_id_to_nfts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_creator column with index
    op.add_column('users', sa.Column(
        'is_creator',
        sa.Boolean(),
        nullable=False,
        server_default='false'
    ))
    op.create_index('ix_users_is_creator', 'users', ['is_creator'])
    
    # Add creator_name column
    op.add_column('users', sa.Column(
        'creator_name',
        sa.String(255),
        nullable=True
    ))
    
    # Add creator_bio column
    op.add_column('users', sa.Column(
        'creator_bio',
        sa.String(1000),
        nullable=True
    ))
    
    # Add creator_avatar_url column
    op.add_column('users', sa.Column(
        'creator_avatar_url',
        sa.String(500),
        nullable=True
    ))


def downgrade() -> None:
    # Drop columns in reverse order
    op.drop_column('users', 'creator_avatar_url')
    op.drop_column('users', 'creator_bio')
    op.drop_column('users', 'creator_name')
    op.drop_index('ix_users_is_creator', 'users')
    op.drop_column('users', 'is_creator')
