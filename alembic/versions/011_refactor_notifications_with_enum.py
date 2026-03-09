"""Refactor notifications table with proper ENUM type and async support.

Revision ID: 011_refactor_notifications_with_enum
Revises: 010_add_ton_wallet_and_stars
Create Date: 2026-03-08 00:00:00.000000

This migration:
- Creates a notificationtype ENUM with idempotent creation
- Creates a simplified notifications table
- Fully compatible with asyncpg and SQLAlchemy 2.0 async
- Ensures ENUM is not dropped on downgrade to allow other tables to reference it
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '011_refactor_notifications_with_enum'
down_revision = '010_add_ton_wallet_and_stars'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create notificationtype ENUM and notifications table with asyncpg support."""
    
    # Create ENUM type with idempotent check - prevents error if already exists
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationtype') THEN
                CREATE TYPE notificationtype AS ENUM (
                    'nft_minted',
                    'nft_sold',
                    'nft_purchased',
                    'nft_listed',
                    'nft_offer_received',
                    'nft_offer_accepted',
                    'listing_sold',
                    'offer_made',
                    'offer_accepted',
                    'payment_received',
                    'payment_pending',
                    'referral_earned',
                    'account_verified',
                    'account_warning',
                    'password_changed',
                    'info',
                    'warning',
                    'error',
                    'success'
                );
            END IF;
        END$$;
        """
    )
    
    # Create notifications table with ENUM column
    # Uses SERIAL for auto-incrementing integer PK (compatible with asyncpg)
    op.create_table(
        'notifications',
        sa.Column(
            'id',
            sa.Integer,
            primary_key=True,
            autoincrement=True,
            nullable=False,
            comment="Primary key - auto-incrementing integer"
        ),
        sa.Column(
            'type',
            postgresql.ENUM(
                'nft_minted',
                'nft_sold',
                'nft_purchased',
                'nft_listed',
                'nft_offer_received',
                'nft_offer_accepted',
                'listing_sold',
                'offer_made',
                'offer_accepted',
                'payment_received',
                'payment_pending',
                'referral_earned',
                'account_verified',
                'account_warning',
                'password_changed',
                'info',
                'warning',
                'error',
                'success',
                name='notificationtype',
                create_type=False,  # Already created above
            ),
            nullable=False,
            comment="Notification type using notificationtype ENUM"
        ),
        sa.Column(
            'message',
            sa.String(1000),
            nullable=False,
            comment="Notification message text"
        ),
        sa.Column(
            'timestamp',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Timestamp when notification was created"
        ),
    )
    
    # Create index on type column for efficient filtering
    op.create_index(
        'ix_notifications_type',
        'notifications',
        ['type'],
        if_not_exists=True
    )
    
    # Create index on timestamp for range queries
    op.create_index(
        'ix_notifications_timestamp',
        'notifications',
        ['timestamp'],
        if_not_exists=True
    )


def downgrade() -> None:
    """Drop notifications table but preserve ENUM for other tables.
    
    Note: The notificationtype ENUM is intentionally NOT dropped here.
    This allows the table to be recreated without losing the ENUM definition,
    and prevents errors if other tables also reference this ENUM.
    """
    
    # Drop indexes first
    op.drop_index('ix_notifications_timestamp', table_name='notifications', if_exists=True)
    op.drop_index('ix_notifications_type', table_name='notifications', if_exists=True)
    
    # Drop the table
    op.drop_table('notifications', if_exists=True)
    
    # IMPORTANT: Do NOT drop the ENUM type (notificationtype)
    # This preserves the type for other tables that may reference it
    # To fully remove the ENUM, run this manually if needed:
    # op.execute("DROP TYPE IF EXISTS notificationtype CASCADE;")
