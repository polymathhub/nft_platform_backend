"""Add activity_logs table for audit trail and user activity tracking - PostgreSQL Safe.

Revision ID: 007_add_activity_logs_table
Revises: 006_add_payments_table
Create Date: 2026-02-20 00:00:00.000000

============================================================================
MIGRATION NOTES
============================================================================

Production improvements:
✓ JSON metadata: Uses sa.text("'{}'::jsonb") for PostgreSQL type casting
✓ String defaults: Uses sa.text() for string literals in database
✓ Indexes: All use if_not_exists=True for idempotent creation
✓ ForeignKey: Explicit CASCADE delete for data integrity
✓ Downgrade: Uses if_exists=True for safe table/index removal
"""
import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

log = logging.getLogger(__name__)

# revision identifiers, used by Alembic.
revision = '007_add_activity_logs_table'
down_revision = '006_add_payments_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create activity_logs table for audit trail and user activity tracking."""
    
    log.info("Starting Migration 007: Create activity_logs table")
    
    # =========================================================================
    # STEP 1: Create activity_logs table with proper type handling
    # =========================================================================
    # Production considerations:
    #   - JSON metadata with default empty object: sa.text("'{}'::jsonb")
    #   - String status column with 'success' default: sa.text("'success'::character varying")
    #   - Proper index strategy for common queries
    #   - Cascade delete for data integrity (ON DELETE CASCADE)
    # =========================================================================
    log.info("Creating activity_logs table...")
    
    op.create_table(
        'activity_logs',
        # Primary Key
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            primary_key=True,
            comment='Activity log record ID'
        ),
        # Foreign Key
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
            comment='User who performed the activity'
        ),
        # Telegram User Info
        sa.Column(
            'telegram_id',
            sa.String(50),
            nullable=True,
            index=True,
            comment='Telegram user ID (if applicable)'
        ),
        sa.Column(
            'telegram_username',
            sa.String(200),
            nullable=True,
            index=True,
            comment='Telegram username (if applicable)'
        ),
        # Activity Tracking
        sa.Column(
            'activity_type',
            sa.String(50),
            nullable=False,
            index=True,
            comment='Type of activity (e.g., user_login, nft_mint, offer_create)'
        ),
        # Resource References
        sa.Column(
            'resource_type',
            sa.String(50),
            nullable=True,
            index=True,
            comment='Type of resource affected (nft, collection, offer, etc.)'
        ),
        sa.Column(
            'resource_id',
            sa.String(100),
            nullable=True,
            index=True,
            comment='ID of the resource affected'
        ),
        # Activity Details
        sa.Column(
            'description',
            sa.String(500),
            nullable=True,
            comment='Human-readable description of the activity'
        ),
        # JSON Metadata (Flexible schema)
        sa.Column(
            'activity_metadata',
            sa.JSON(),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='JSON object with activity-specific metadata'
        ),
        # Request Context
        sa.Column(
            'ip_address',
            sa.String(50),
            nullable=True,
            comment='IP address of the requester'
        ),
        sa.Column(
            'user_agent',
            sa.String(500),
            nullable=True,
            comment='User agent string from HTTP request'
        ),
        # Status
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default=sa.text("'success'::character varying"),
            comment='Status of the activity (success, pending, failed)'
        ),
        sa.Column(
            'error_message',
            sa.Text(),
            nullable=True,
            comment='Error message if status is failed'
        ),
        # Timestamps
        sa.Column(
            'timestamp',
            sa.DateTime(timezone=True),
            nullable=False,
            comment='When the activity occurred'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='When this log record was created (UTC)'
        ),
        # Constraints
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
            name='fk_activity_logs_user_id'
        ),
    )
    log.info("  ✓ activity_logs table created")
    
    # =========================================================================
    # STEP 2: Create indexes for common query patterns
    # =========================================================================
    # Index strategy:
    #   - Composite: (user_id, timestamp) - "get user's recent activity"
    #   - Composite: (activity_type, timestamp) - "get activity type history"
    #   - Composite: (resource_type, resource_id) - "get resource's activity trail"
    #   - Composite: (telegram_id, timestamp) - "get user's telegram activity"
    # =========================================================================
    log.info("Creating indexes for query optimization...")
    
    op.create_index(
        'ix_activity_logs_user_timestamp',
        'activity_logs',
        ['user_id', 'timestamp'],
        if_not_exists=True
    )
    op.execute(
        "COMMENT ON INDEX ix_activity_logs_user_timestamp IS "
        "'Composite index for recent user activity queries';"
    )
    log.info("  ✓ Index: ix_activity_logs_user_timestamp")
    
    op.create_index(
        'ix_activity_logs_activity_type',
        'activity_logs',
        ['activity_type', 'timestamp'],
        if_not_exists=True
    )
    op.execute(
        "COMMENT ON INDEX ix_activity_logs_activity_type IS "
        "'Composite index for activity type history queries';"
    )
    log.info("  ✓ Index: ix_activity_logs_activity_type")
    
    op.create_index(
        'ix_activity_logs_resource',
        'activity_logs',
        ['resource_type', 'resource_id'],
        if_not_exists=True
    )
    op.execute(
        "COMMENT ON INDEX ix_activity_logs_resource IS "
        "'Composite index for resource activity trail queries';"
    )
    log.info("  ✓ Index: ix_activity_logs_resource")
    
    op.create_index(
        'ix_activity_logs_telegram',
        'activity_logs',
        ['telegram_id', 'timestamp'],
        if_not_exists=True
    )
    op.execute(
        "COMMENT ON INDEX ix_activity_logs_telegram IS "
        "'Composite index for telegram user activity queries';"
    )
    log.info("  ✓ Index: ix_activity_logs_telegram")
    
    log.info("Migration 007 upgrade completed successfully")


def downgrade() -> None:
    """Drop activity_logs table and indexes safely."""
    
    log.info("Starting Migration 007 downgrade...")
    
    # =========================================================================
    # STEP 1: Drop indexes in reverse order
    # =========================================================================
    log.info("Dropping indexes...")
    
    op.drop_index('ix_activity_logs_telegram', table_name='activity_logs', if_exists=True)
    log.info("  ✓ Dropped index: ix_activity_logs_telegram")
    
    op.drop_index('ix_activity_logs_resource', table_name='activity_logs', if_exists=True)
    log.info("  ✓ Dropped index: ix_activity_logs_resource")
    
    op.drop_index('ix_activity_logs_activity_type', table_name='activity_logs', if_exists=True)
    log.info("  ✓ Dropped index: ix_activity_logs_activity_type")
    
    op.drop_index('ix_activity_logs_user_timestamp', table_name='activity_logs', if_exists=True)
    log.info("  ✓ Dropped index: ix_activity_logs_user_timestamp")
    
    # =========================================================================
    # STEP 2: Drop table
    # =========================================================================
    log.info("Dropping activity_logs table...")
    
    op.drop_table('activity_logs', if_exists=True)
    log.info("  ✓ Dropped activity_logs table")
    
    log.info("Migration 007 downgrade completed")
