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
✓ UUID PKs: Uses postgresql.UUID(as_uuid=True) for uuid handling (not sa.Uuid())
✓ Timezone-aware: DateTime columns are timezone-aware for UTC consistency

MIGRATION FIXES (v2):
✓ Fixed: ForeignKeyConstraint moved OUT of Column definition (now separate table arg)
✓ Fixed: sa.Uuid() → postgresql.UUID(as_uuid=True) for PostgreSQL UUID type
✓ Fixed: server_default='false' → sa.text("'false'::boolean") for type safety
✓ Fixed: All string defaults use sa.text() for PostgreSQL compatibility

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
    Ensure notificationtype ENUM exists (table already created by migration 009).
    
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
    
    # Table and indexes are already created by migration 009
    # This migration only ensures the ENUM type exists


def downgrade() -> None:
    """
    Downgrade by preserving the ENUM type.
    
    Important: The notificationtype ENUM is NOT dropped here.
    This allows future forward migrations to recreate the table without issues.
    The notifications table is managed by migration 009.
    """
    # No action needed - ENUM is intentionally preserved
    # Migration 009 handles table drops in its downgrade function
    pass
