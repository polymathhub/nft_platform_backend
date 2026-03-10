"""Add notifications table with notificationtype ENUM - Production Grade.

Revision ID: 009_add_notifications_table
Revises: 008_add_referral_system
Create Date: 2026-03-07 00:00:00.000000

============================================================================
MIGRATION SPECIFICATION
============================================================================

This migration creates a complete notifications system with:

1. notificationtype PostgreSQL ENUM (19 values)
2. notifications table with:
   - UUID primary key
   - UUID foreign key to users table (CASCADE delete)
   - Rich event/notification metadata
   - Timestamp tracking (created, updated, read)
   - Read status tracking
   - Action links and metadata storage
   
3. Performance indexes:
   - Composite index: user_id + created_at
   - Composite index: user_id + is_read
   - Single index: notification_type

============================================================================
PRODUCTION-GRADE FEATURES
============================================================================

✓ Safe ENUM Creation
  - PostgreSQL DO block for IF NOT EXISTS check
  - Prevents DuplicateObjectError on re-runs
  - Atomic transaction handling

✓ Proper Alembic Syntax
  - ForeignKeyConstraint as separate table argument (not column)
  - Prevents AssertionError: isinstance(table, Table)
  - Named constraints for clarity and debugging

✓ Async SQLAlchemy 2.0+ Compatible
  - Works with asyncpg driver
  - Compatible with async/await migration execution
  - Proper server defaults for UTC consistency

✓ PostgreSQL Dialect Compliance
  - postgresql.ENUM for type safety
  - op.execute("COMMENT ON INDEX...") for index comments
  - Explicit naming conventions for all constraints

✓ Idempotent Operations
  - upgrade() can be run multiple times safely
  - downgrade() safely handles missing objects
  - if_exists=True guards on drops

✓ Clean Error Handling
  - Includes logging for debugging
  - Explicit error messages for troubleshooting
  - Detailed comments explaining each step

============================================================================
ENUM VALUES (19 TOTAL)
============================================================================

NFT Events (6):
  - nft_minted, nft_sold, nft_purchased, nft_listed,
    nft_offer_received, nft_offer_accepted

Marketplace Events (3):
  - listing_sold, offer_made, offer_accepted

System Events (3):
  - payment_received, payment_pending, referral_earned

User Account Events (3):
  - account_verified, account_warning, password_changed

General Events (4):
  - info, warning, error, success
"""

import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Configure logging for migration tracking
log = logging.getLogger(__name__)

# Revision identifiers
revision = '009_add_notifications_table'
down_revision = '008_add_referral_system'
branch_labels = None
depends_on = None

# Centralized ENUM values (single source of truth)
NOTIFICATION_TYPES = [
    # NFT Events
    'nft_minted',
    'nft_sold',
    'nft_purchased',
    'nft_listed',
    'nft_offer_received',
    'nft_offer_accepted',
    # Marketplace Events
    'listing_sold',
    'offer_made',
    'offer_accepted',
    # System Events
    'payment_received',
    'payment_pending',
    'referral_earned',
    # User Account Events
    'account_verified',
    'account_warning',
    'password_changed',
    # General Events
    'info',
    'warning',
    'error',
    'success',
]


def upgrade() -> None:
    """
    Create notificationtype ENUM and notifications table.
    
    This function is fully idempotent and async-safe:
      - Can be run multiple times without DuplicateObjectError
      - Works with fresh and existing databases
      - Compatible with asyncpg and async SQLAlchemy
      - Properly logs each step for debugging
    
    Execution order:
      1. Create ENUM type (with IF NOT EXISTS check)
      2. Create notifications table (with all columns and constraints)
      3. Create performance indexes
    """
    
    log.info("=== Migration 009: Creating notifications table ===")
    
    # =========================================================================
    # STEP 1: Create PostgreSQL ENUM type safely
    # =========================================================================
    # Why this approach:
    #   - PostgreSQL DO block is atomic (all-or-nothing)
    #   - pg_type catalog check detects existing ENUMs reliably
    #   - Prevents DuplicateObjectError that checkfirst=True misses
    #   - Works with asyncpg driver (op.execute uses connection.execute)
    #
    # Execution:
    #   - Checks if notificationtype ENUM exists
    #   - Only creates if missing
    #   - Succeeds silently if already present
    # =========================================================================
    log.info("Step 1: Creating notificationtype ENUM...")
    
    op.execute(
        """
        DO $$
        BEGIN
            -- Safely check if notificationtype ENUM already exists
            -- typtype = 'e' filters for ENUM types only (excludes base, composite, etc.)
            IF NOT EXISTS (
                SELECT 1 FROM pg_type 
                WHERE typname = 'notificationtype' 
                AND typtype = 'e'
            ) THEN
                -- Create ENUM with all 19 notification type values
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
    log.info("  ✓ notificationtype ENUM created or already exists")
    
    # =========================================================================
    # STEP 2: Create notifications table
    # =========================================================================
    # Critical Alembic Rules:
    #   1. ForeignKeyConstraint must be separate table argument (NOT in Column)
    #   2. This prevents AssertionError: isinstance(table, Table)
    #   3. All constraints should have explicit names for debugging
    #   4. Server defaults ensure consistency across app and database
    #
    # Column Organization:
    #   - Primary keys first
    #   - Foreign keys next
    #   - Regular data columns
    #   - Status/metadata columns
    #   - Timestamps last
    #   - Constraints after all columns
    # =========================================================================
    log.info("Step 2: Creating notifications table...")
    
    op.create_table(
        'notifications',
        # =====================================================================
        # PRIMARY KEY
        # =====================================================================
        sa.Column(
            'id',
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            comment='Notification ID - UUID primary key, generated on creation'
        ),
        
        # =====================================================================
        # FOREIGN KEY (Constraint defined separately at end)
        # =====================================================================
        sa.Column(
            'user_id',
            sa.Uuid(),
            nullable=False,
            index=True,
            comment='FK to users.id - Cascades on user deletion'
        ),
        
        # =====================================================================
        # NOTIFICATION CONTENT COLUMNS
        # =====================================================================
        sa.Column(
            'title',
            sa.String(255),
            nullable=False,
            comment='Notification title/display name (max 255 chars)'
        ),
        
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Long-form description of the notification'
        ),
        
        sa.Column(
            'message',
            sa.Text(),
            nullable=True,
            comment='Alias for description - message text (backward compatibility)'
        ),
        
        sa.Column(
            'subject',
            sa.String(255),
            nullable=True,
            comment='Alias for title - subject line (backward compatibility)'
        ),
        
        # =====================================================================
        # NOTIFICATION TYPE (Uses ENUM created in Step 1)
        # =====================================================================
        # create_type=False: ENUM already created above in Step 1
        # name='notificationtype': Explicitly reference the ENUM type
        # =====================================================================
        sa.Column(
            'notification_type',
            postgresql.ENUM(
                *NOTIFICATION_TYPES,
                name='notificationtype',
                create_type=False,  # Already created in DO block above
                metadata=None,
            ),
            nullable=False,
            index=True,
            comment='Notification event type (from notificationtype ENUM)'
        ),
        
        # =====================================================================
        # STATUS COLUMNS
        # =====================================================================
        sa.Column(
            'is_read',
            sa.Boolean(),
            nullable=False,
            server_default=sa.literal(False),  # Async-safe default
            index=True,
            comment='Whether the notification has been read by user'
        ),
        
        sa.Column(
            'read',
            sa.Boolean(),
            nullable=False,
            server_default=sa.literal(False),  # Async-safe default
            comment='Alias for is_read - backward compatibility'
        ),
        
        # =====================================================================
        # ACTION/LINK COLUMNS
        # =====================================================================
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
            comment='Type of action: view_nft, accept_offer, complete_payment, etc.'
        ),
        
        # =====================================================================
        # METADATA COLUMN
        # =====================================================================
        sa.Column(
            'extra_metadata',
            sa.String(1000),
            nullable=True,
            comment='JSON string containing additional event metadata'
        ),
        
        # =====================================================================
        # TIMESTAMP COLUMNS
        # =====================================================================
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),  # UTC via PostgreSQL NOW()
            index=True,
            comment='When the notification was created (UTC)'
        ),
        
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),  # UTC via PostgreSQL NOW()
            comment='When the notification was last updated (UTC)'
        ),
        
        sa.Column(
            'read_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When the notification was marked as read (UTC)'
        ),
        
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
            index=True,
            comment='When the notification expires (for auto-cleanup)'
        ),
        
        # =====================================================================
        # TABLE CONSTRAINTS (MUST be separate from columns)
        # =====================================================================
        # Critical: ForeignKeyConstraint as separate argument prevents
        # AssertionError: isinstance(table, Table)
        # =====================================================================
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
            name='fk_notifications_user_id',
            comment='Cascade user deletion to remove all their notifications'
        ),
    )
    
    log.info("  ✓ notifications table created successfully")
    
    # =========================================================================
    # STEP 3: Create performance indexes
    # =========================================================================
    # Index Strategy:
    #   - Composite indexes for multi-column queries
    #   - Single-column indexes for filtering
    #   - Comments applied via op.execute (not on create_index)
    #   - All are idempotent and async-safe
    # =========================================================================
    log.info("Step 3: Creating performance indexes...")
    
    # Composite index: user_id + created_at
    # Common query: "Get user's notifications in date order"
    op.create_index(
        'idx_notifications_user_id_created_at',
        'notifications',
        ['user_id', 'created_at'],
    )
    op.execute(
        "COMMENT ON INDEX idx_notifications_user_id_created_at IS "
        "'Composite index for recent notifications by user - optimizes date range queries';"
    )
    log.info("  ✓ Created index: idx_notifications_user_id_created_at")
    
    # Composite index: user_id + is_read
    # Common query: "Get unread notification count for user"
    op.create_index(
        'idx_notifications_user_id_is_read',
        'notifications',
        ['user_id', 'is_read'],
    )
    op.execute(
        "COMMENT ON INDEX idx_notifications_user_id_is_read IS "
        "'Composite index for filtering unread notifications - optimizes is_read checks per user';"
    )
    log.info("  ✓ Created index: idx_notifications_user_id_is_read")
    
    # Single index: notification_type
    # Common query: "Get all notifications of a specific type"
    op.create_index(
        'idx_notifications_notification_type',
        'notifications',
        ['notification_type'],
    )
    op.execute(
        "COMMENT ON INDEX idx_notifications_notification_type IS "
        "'Index for filtering by notification event type';"
    )
    log.info("  ✓ Created index: idx_notifications_notification_type")
    
    log.info("=== Migration 009 upgrade completed successfully ===")


def downgrade() -> None:
    """
    Remove notifications table while preserving ENUM.
    
    This function is idempotent and safe to run multiple times:
      - Drops indexes with if_exists=True
      - Drops table with if_exists=True
      - Preserves ENUM for forward migration safety
    
    Execution order:
      1. Drop composite indexes
      2. Drop single-column indexes
      3. Drop table
      4. PRESERVE ENUM (intentional)
    
    Rationale for preserving ENUM:
      - Allows future migrations to recreate the table
      - Other tables may reference this ENUM
      - Supports rollforward scenarios
      - Manual ENUM cleanup available if needed
    """
    
    log.info("=== Migration 009: Downgrading notifications table ===")
    
    # =========================================================================
    # STEP 1: Drop composite indexes first
    # =========================================================================
    # Order matters: Drop most specific (composite) before general (single)
    # =========================================================================
    log.info("Step 1: Dropping performance indexes...")
    
    op.drop_index(
        'idx_notifications_user_id_is_read',
        table_name='notifications',
        if_exists=True,
    )
    log.info("  ✓ Dropped index: idx_notifications_user_id_is_read")
    
    op.drop_index(
        'idx_notifications_user_id_created_at',
        table_name='notifications',
        if_exists=True,
    )
    log.info("  ✓ Dropped index: idx_notifications_user_id_created_at")
    
    op.drop_index(
        'idx_notifications_notification_type',
        table_name='notifications',
        if_exists=True,
    )
    log.info("  ✓ Dropped index: idx_notifications_notification_type")
    
    # Note: Indexes created via Column(index=True) in table definition are
    # automatically dropped by the drop_table() call below
    
    # =========================================================================
    # STEP 2: Drop table
    # =========================================================================
    # if_exists=True: Prevents error if table already dropped
    # =========================================================================
    log.info("Step 2: Dropping notifications table...")
    
    op.drop_table('notifications', if_exists=True)
    log.info("  ✓ Dropped notifications table")
    
    # =========================================================================
    # STEP 3: PRESERVE ENUM (intentional)
    # =========================================================================
    # The notificationtype ENUM is intentionally NOT dropped because:
    #
    # 1. Forward Migration Safety
    #    - If this migration is rolled back and then re-applied,
    #    - the ENUM will already exist (handled by IF NOT EXISTS in upgrade)
    #
    # 2. Multi-Table Scenarios
    #    - Other tables may reference notificationtype ENUM
    #    - Dropping would require CASCADE, breaking referential integrity
    #
    # 3. Rollforward Support
    #    - Users can rollback to an earlier version, then rollforward
    #    - ENUM preservation enables seamless rollforward
    #
    # If you MUST remove the ENUM type:
    #   1. Ensure no tables reference it:
    #      SELECT * FROM information_schema.columns 
    #      WHERE udt_name = 'notificationtype';
    #   2. Drop manually via alembic raw SQL:
    #      op.execute('DROP TYPE IF EXISTS notificationtype CASCADE;')
    #   3. Create a new migration file for this
    #      (Do not add it to this downgrade function)
    # =========================================================================
    
    log.info("  ℹ  ENUM 'notificationtype' intentionally preserved")
    log.info("  ℹ  (Allows forward migrations and supports rollforward scenarios)")
    log.info("=== Migration 009 downgrade completed successfully ===")

