"""Add referral and stars columns to users table

Revision ID: 018_add_referral_and_stars_columns_to_users
Revises: 017_add_photo_url_column
Create Date: 2026-03-31 13:50:00.000000

This migration adds the missing columns for the referral system and
stars balance tracking to the users table. These columns are required
for the User model but were not created in previous migrations.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '018_add_referral_and_stars_columns_to_users'
down_revision = '017_add_photo_url_column'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add referral_code column
    op.add_column('users', sa.Column(
        'referral_code',
        sa.String(50),
        unique=True,
        nullable=True,
        index=True
    ))

    # Add referred_by_id column (foreign key to users.id)
    op.add_column('users', sa.Column(
        'referred_by_id',
        postgresql.UUID(as_uuid=True),
        nullable=True,
        index=True
    ))
    
    # Add foreign key constraint for referred_by_id
    op.create_foreign_key(
        'fk_users_referred_by_id',
        'users',
        'users',
        ['referred_by_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add referral_locked_at column
    op.add_column('users', sa.Column(
        'referral_locked_at',
        sa.DateTime(),
        nullable=True
    ))

    # Add stars_balance column
    op.add_column('users', sa.Column(
        'stars_balance',
        sa.Float(),
        nullable=False,
        server_default='0.0'
    ))

    # Add total_stars_earned column
    op.add_column('users', sa.Column(
        'total_stars_earned',
        sa.Float(),
        nullable=False,
        server_default='0.0'
    ))

    # Add total_stars_spent column
    op.add_column('users', sa.Column(
        'total_stars_spent',
        sa.Float(),
        nullable=False,
        server_default='0.0'
    ))


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_users_referred_by_id', 'users', type_='foreignkey')
    
    # Drop all added columns
    op.drop_column('users', 'total_stars_spent')
    op.drop_column('users', 'total_stars_earned')
    op.drop_column('users', 'stars_balance')
    op.drop_column('users', 'referral_locked_at')
    op.drop_column('users', 'referred_by_id')
    op.drop_column('users', 'referral_code')
