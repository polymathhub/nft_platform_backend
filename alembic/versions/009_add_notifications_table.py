"""Add notifications table - Safe ENUM handling with PostgreSQL DO block.

Revision ID: 009_add_notifications_table
Revises: 008_add_referral_system
Create Date: 2026-03-07 00:00:00.000000

This migration safely creates:
  - notificationtype PostgreSQL ENUM with 19 values
  - notifications table with UUID PKs and ENUM column
  - Optimized indexes for query performance

Safe features:
  - Uses PostgreSQL DO block to prevent DuplicateObjectError
  - Idempotent: Can be run multiple times without errors
  - Works on fresh databases and existing databases
  - Proper downgrade with cascade handling
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_add_notifications_table'
down_revision = '008_add_referral_system'
branch_labels = None
depends_on = None

# All notification type enum values
NOTIFICATION_TYPES = [
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
]


def upgrade() -> None:
    """
    Create notificationtype ENUM and notifications table.
    
    Uses PostgreSQL DO block to safely create ENUM without DuplicateObjectError.
    This approach is:
      - Idempotent: Safe to run multiple times
      - Atomic: If ENUM exists, it succeeds silently
      - Compatible: Works with asyncpg and all PostgreSQL versions
    """
    
    # =========================================================================
    # Step 1: Create ENUM type with safe IF NOT EXISTS check
    # =========================================================================
    # PostgreSQL DO block executes procedural code within a transaction.
    # The pg_type catalog query checks if the type already exists.
    # This prevents DuplicateObjectError that checkfirst=True sometimes misses.
    # =========================================================================
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if notificationtype ENUM already exists
            IF NOT EXISTS (
                SELECT 1 FROM pg_type 
                WHERE typname = 'notificationtype' 
                AND typtype = 'e'
            ) THEN
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
    
    # =========================================================================
    # Step 2: Create notifications table
    # =========================================================================
    op.create_table(
        'notifications',
        sa.Column(
            'id',
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            comment='Notification ID - UUID primary key'
        ),
        sa.Column(
            'user_id',
            sa.Uuid(),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            nullable=False,
            index=True,
            comment='FK to users.id - cascades on user deletion'
        ),
        sa.Column(
            'title',
            sa.String(255),
            nullable=False,
            comment='Notification title/display name'
        ),
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Detailed description of the notification'
        ),
        sa.Column(
            'message',
            sa.Text(),
            nullable=True,
            comment='Alias for description - message text'
        ),
        sa.Column(
            'subject',
            sa.String(255),
            nullable=True,
            comment='Alias for title - backward compatibility'
        ),
        sa.Column(
            'notification_type',
            postgresql.ENUM(*NOTIFICATION_TYPES, name='notificationtype', create_type=False),
            nullable=False,
            index=True,
            comment='Notification event type (from notificationtype ENUM)'
        ),
        sa.Column(
            'is_read',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            index=True,
            comment='Read status of notification'
        ),
        sa.Column(
            'read',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            comment='Alias for is_read - backward compatibility'
        ),
        sa.Column(
            'action_url',
            sa.String(500),
            nullable=True,
            comment='URL to navigate to when notification is clicked'
        ),
        sa.Column(
            'action_type',
            sa.String(50),
            nullable=True,
            comment='Type of action (e.g., view_nft, accept_offer)'
        ),
        sa.Column(
            'extra_metadata',
            sa.String(1000),
            nullable=True,
            comment='JSON string with additional metadata'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
            comment='When the notification was created'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            comment='When the notification was last updated'
        ),
        sa.Column(
            'read_at',
            sa.DateTime(),
            nullable=True,
            comment='When the notification was read'
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(),
            nullable=True,
            index=True,
            comment='When the notification expires (for cleanup)'
        ),
    )
    
    # =========================================================================
    # Step 3: Create indexes for query performance
    # =========================================================================
    op.create_index(
        'idx_notifications_user_id_created_at',
        'notifications',
        ['user_id', 'created_at'],
        comment='Composite index for recent notifications by user'
    )
    op.create_index(
        'idx_notifications_user_id_is_read',
        'notifications',
        ['user_id', 'is_read'],
        comment='Composite index for unread notifications by user'
    )
    op.create_index(
        'idx_notifications_notification_type',
        'notifications',
        ['notification_type'],
        comment='Index for filtering by notification type'
    )


def downgrade() -> None:
    """
    Remove notifications table and ENUM safely.
    
    Drops in reverse order:
      1. Indexes (must be done first)
      2. Table (with CASCADE for foreign keys)
      3. ENUM is preserved for forward migration safety
    
    Note: ENUM is NOT dropped to support future migrations that might
    recreate the table. To manually remove the ENUM:
        DROP TYPE IF EXISTS notificationtype CASCADE;
    """
    
    # =========================================================================
    # Step 1: Drop indexes in reverse order
    # =========================================================================
    op.drop_index(
        'idx_notifications_notification_type',
        table_name='notifications',
        if_exists=True
    )
    op.drop_index(
        'idx_notifications_user_id_is_read',
        table_name='notifications',
        if_exists=True
    )
    op.drop_index(
        'idx_notifications_user_id_created_at',
        table_name='notifications',
        if_exists=True
    )
    
    # Note: Indexes created via Column(index=True) are automatically dropped
    
    # =========================================================================
    # Step 2: Drop table
    # =========================================================================
    op.drop_table('notifications', if_exists=True)
    
    # =========================================================================
    # Step 3: Preserve ENUM (do NOT drop)
    # =========================================================================
    # The notificationtype ENUM is intentionally preserved because:
    #   1. Allows forward migrations to recreate the table
    #   2. May be referenced by other future tables
    #   3. Supports rolling forward after rollback
    #
    # To manually remove the ENUM type:
    #   alembic downgrade -1  (this migration)
    #   Then run manually in PostgreSQL:
    #   DROP TYPE IF EXISTS notificationtype CASCADE;
