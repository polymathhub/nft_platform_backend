"""Add photo_url column to users table for Telegram profile pictures

Revision ID: 017_add_photo_url_column
Revises: 016_add_creator_columns
Create Date: 2026-03-31 03:35:00.000000

This migration adds a photo_url column to the users table to store the
Telegram profile picture URL that comes from the initData. This allows
users to display their Telegram profile pictures in the app.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '017_add_photo_url_column'
down_revision = '016_add_creator_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add photo_url column
    op.add_column('users', sa.Column(
        'photo_url',
        sa.String(500),
        nullable=True
    ))


def downgrade() -> None:
    # Drop column
    op.drop_column('users', 'photo_url')
