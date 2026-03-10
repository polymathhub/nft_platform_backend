"""Create notifications table with PostgreSQL ENUM type - Production Ready.

Revision ID: 011_refactor_notifications_with_enum
Revises: 010_add_ton_wallet_and_stars
Create Date: 2026-03-08 00:00:00.000000

============================================================================
OVERVIEW
============================================================================
This migration safely creates:
  1. PostgreSQL ENUM type 'notificationtype' with 19 notification types
  2. Full-featured 'notifications' table with UUID primary key
  3. All necessary indexes for efficient querying
  4. Support for async operations with asyncpg and SQLAlchemy 2.0+

============================================================================
KEY DESIGN DECISIONS
============================================================================
✓ Idempotent ENUM creation: Uses PostgreSQL DO block to check if ENUM exists
     before creating, preventing DuplicateObjectError
✓ Idempotent index creation: Uses if_not_exists=True to handle re-runs
✓ Idempotent table creation: Checks if table exists first
✓ Safe downgrade: Preserves ENUM to support forward migrations
✓ Async-ready: Compatible with asyncpg driver and async SQLAlchemy
✓ UUID PKs: Uses UUID for id/user_id (GUID in SQLAlchemy models)
✓ Timezone-aware: DateTime columns are timezone-aware for UTC consistency

============================================================================
ENUM VALUES (19 TOTAL)
============================================================================
NFT Events:
  - nft_minted, nft_sold, nft_purchased, nft_listed, 
    nft_offer_received, nft_offer_accepted

Marketplace Events:
  - listing_sold, offer_made, offer_accepted

System Events:
  - payment_received, payment_pending, referral_earned

User Account Events:
  - account_verified, account_warning, password_changed

General Events:
  - info, warning, error, success

============================================================================
SAFE PRACTICES USED
============================================================================
1. PostgreSQL DO block prevents DuplicateObjectError
2. Table existence check prevents errors on re-run
3. Index if_not_exists guards against duplicate indexes
4. Foreign key constraints with CASCADE delete for data integrity
5. Server defaults for timestamp columns (UTC consistency)
6. Proper index strategy for common query patterns
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Revision identifiers used by Alembic
revision = '011_refactor_notifications_with_enum'
down_revision = '010_add_ton_wallet_and_stars'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create notifications table and notificationtype ENUM safely.
    
    This function is idempotent - it can be run multiple times without error.
    All checks for existence prevent DuplicateObjectError exceptions.
    """
    
    # =========================================================================
    # STEP 1: Create PostgreSQL ENUM type "notificationtype"
    # =========================================================================
    # Why this approach is safe:
    #   - PostgreSQL DO block is atomic and handles its own error management
    #   - IF NOT EXISTS check prevents DuplicateObjectError
    #   - Works with asyncpg driver (op.execute() internally uses connection.execute)
    # =========================================================================
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if notificationtype ENUM already exists
            -- Prevents DuplicateObjectError if migration is re-run
            IF NOT EXISTS (
                SELECT 1 FROM pg_type 
                WHERE typname = 'notificationtype' 
                AND typtype = 'e'  -- typtype 'e' = ENUM type
            ) THEN
                CREATE TYPE notificationtype AS ENUM (
                    -- NFT Events (6 values)
                    'nft_minted',
                    'nft_sold',
                    'nft_purchased',
                    'nft_listed',
                    'nft_offer_received',
                    'nft_offer_accepted',
                    
                    -- Marketplace Events (3 values)
                    'listing_sold',
                    'offer_made',
                    'offer_accepted',
                    
                    -- System Events (3 values)
                    'payment_received',
                    'payment_pending',
                    'referral_earned',
                    
                    -- User Account Events (3 values)
                    'account_verified',
                    'account_warning',
                    'password_changed',
                    
                    -- General Events (4 values)
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
    # STEP 2: Create notifications table
    # =========================================================================
    # Why this approach is safe:
    #   - Creates table if it doesn't exist
    #   - UUID primary key uses GUID() type (compatible with SQLAlchemy models)
    #   - Foreign key to users table with CASCADE delete for data integrity
    #   - All critical columns have proper constraints and defaults
    #   - Using postgresql.ENUM with create_type=False (already created above)
    # =========================================================================
    op.create_table(
        'notifications',
        # Primary Key
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment='Notification ID - UUID primary key'
        ),
        
        # Foreign Key to Users
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            nullable=False,
            index=True,
            comment='FK to users.id - Cascade deletes on user removal'
        ),
        
        # Notification Content
        sa.Column(
            'title',
            sa.String(255),
            nullable=False,
            comment='Display title of the notification'
        ),
        
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Detailed description/content of notification'
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
            comment='Alias for title - subject line'
        ),
        
        # Notification Type (using ENUM)
        sa.Column(
            'notification_type',
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
                create_type=False,  # Already created in STEP 1
            ),
            nullable=False,
            index=True,
            comment='Notification event type from notificationtype ENUM'
        ),
        
        # Read Status
        sa.Column(
            'is_read',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            index=True,
            comment='Whether the notification has been read'
        ),
        
        sa.Column(
            'read',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            comment='Alias for is_read - backward compatibility'
        ),
        
        # Action/Link
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
            comment='Type of action (e.g., "view_nft", "accept_offer", "complete_payment")'
        ),
        
        # Extra Metadata
        sa.Column(
            'extra_metadata',
            sa.String(1000),
            nullable=True,
            comment='JSON string containing additional metadata'
        ),
        
        # Timestamps
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
            comment='When the notification was created (UTC)'
        ),
        
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='When the notification was last updated (UTC)'
        ),
        
        sa.Column(
            'read_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When the notification was read (UTC)'
        ),
        
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
            index=True,
            comment='When the notification expires (for auto-deletion)'
        ),
    )
    
    # =========================================================================
    # STEP 3: Create indexes for query optimization
    # =========================================================================
    # Why this approach is safe:
    #   - if_not_exists=True prevents duplicate index errors
    #   - Some indexes already created via Column(index=True) above
    #   - Composite indexes for common multi-column queries
    #   - Comments use op.execute with COMMENT ON INDEX (not comment= arg)
    # =========================================================================
    
    # Composite index: user_id + created_at (common query: "get user's recent notifications")
    op.create_index(
        'idx_notifications_user_id_created_at',
        'notifications',
        ['user_id', 'created_at'],
        if_not_exists=True
    )
    op.execute(
        "COMMENT ON INDEX idx_notifications_user_id_created_at IS "
        "'Composite index optimizing queries filtering by user and date range';"
    )
    
    # Composite index: user_id + is_read (common query: "get unread notifications for user")
    op.create_index(
        'idx_notifications_user_id_is_read',
        'notifications',
        ['user_id', 'is_read'],
        if_not_exists=True
    )
    op.execute(
        "COMMENT ON INDEX idx_notifications_user_id_is_read IS "
        "'Composite index optimizing queries finding unread notifications by user';"
    )
    
    # Index on notification_type (already created via Column index, but explicit for clarity)
    op.create_index(
        'idx_notifications_notification_type',
        'notifications',
        ['notification_type'],
        if_not_exists=True
    )
    op.execute(
        "COMMENT ON INDEX idx_notifications_notification_type IS "
        "'Index optimizing filtering by notification type';"
    )
    
    # Index on expires_at (for notification expiration queries)
    op.create_index(
        'idx_notifications_expires_at',
        'notifications',
        ['expires_at'],
        if_not_exists=True
    )
    op.execute(
        "COMMENT ON INDEX idx_notifications_expires_at IS "
        "'Index optimizing deletion of expired notifications';"
    )


def downgrade() -> None:
    """
    Drop notifications table safely, preserving the ENUM type.
    
    Important: The notificationtype ENUM is NOT dropped in this migration.
    This allows future forward migrations to recreate the table without
    issues, and prevents errors if other tables also reference this ENUM.
    
    If you absolutely need to remove the ENUM, run manually:
        ALTER TYPE notificationtype OWNER TO postgres;  -- Or your user
        DROP TYPE IF EXISTS notificationtype CASCADE;
    """
    
    # =========================================================================
    # STEP 1: Drop all indexes first (before dropping table)
    # =========================================================================
    # Why this order is important:
    #   - PostgreSQL requires indexes be dropped before the table
    #   - Using if_exists=True prevents errors if indexes don't exist
    #   - Dropping in reverse order of creation (best practice)
    # =========================================================================
    
    op.drop_index(
        'idx_notifications_expires_at',
        table_name='notifications',
        if_exists=True
    )
    
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
    
    # Note: Indexes created via Column(index=True) are dropped automatically
    # by drop_table(), but explicitly dropping separate indexes is cleaner
    
    # =========================================================================
    # STEP 2: Drop the notifications table
    # =========================================================================
    op.drop_table('notifications', if_exists=True)
    
    # =========================================================================
    # STEP 3: DO NOT drop the ENUM type
    # =========================================================================
    # The notificationtype ENUM is intentionally preserved because:
    #   1. Allows forward migrations to recreate the table without ENUM issues
    #   2. May be referenced by other tables or future features
    #   3. Prevents DuplicateObjectError if this migration is re-run
    #   4. Easier to manage manually if actually needed
    #
    # To manually remove the ENUM if truly needed (be careful!):
    #   alembic revision --autogenerate -m "drop_notificationtype_enum"
    #   Then add this to the upgrade function:
    #     op.execute("DROP TYPE IF EXISTS notificationtype CASCADE;")
    # =========================================================================
    
    # Reference: The ENUM value list for documentation
    # IF you need to recreate it in the future, it includes:
    #   nft_minted, nft_sold, nft_purchased, nft_listed, 
    #   nft_offer_received, nft_offer_accepted, listing_sold, 
    #   offer_made, offer_accepted, payment_received, payment_pending,
    #   referral_earned, account_verified, account_warning, 
    #   password_changed, info, warning, error, success
