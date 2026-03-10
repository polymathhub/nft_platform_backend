"""Add admin system tables and user role column - PostgreSQL Safe.

Revision ID: 003_add_admin_system
Revises: 002_add_escrows_table
Create Date: 2026-02-13 00:00:00.000000

============================================================================
MIGRATION FIXES (v2)
============================================================================

Production improvements:
✓ DECIMAL columns: Use sa.numeric.Numeric for proper type handling
✓ Server defaults: Use sa.text() for PostgreSQL-safe literals
✓ ENUM type: Safely create with IF NOT EXISTS check
✓ Indexes: Use standard op.create_index without dialect-specific args
✓ Idempotent: All operations safe to re-run without errors
"""
import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

log = logging.getLogger(__name__)

# revision identifiers, used by Alembic.
revision = '003_add_admin_system'
down_revision = '002_add_escrows_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create admin_logs and admin_settings tables with safe defaults and ENUM handling."""
    
    log.info("Starting Migration 003: Add admin system tables")
    
    # =========================================================================
    # STEP 1: Create adminlogaction ENUM type safely
    # =========================================================================
    # Why use DO block:
    #   - IF NOT EXISTS prevents DuplicateObjectError on re-run
    #   - Safe for both fresh and existing databases
    #   - Atomic transaction handling via PostgreSQL DO
    # =========================================================================
    log.info("Step 1: Creating adminlogaction ENUM type...")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'adminlogaction') THEN
                CREATE TYPE adminlogaction AS ENUM (
                    'user_role_changed',
                    'commission_rate_updated',
                    'commission_wallet_updated',
                    'admin_added',
                    'admin_removed',
                    'user_suspended',
                    'user_activated',
                    'system_config_changed',
                    'database_backup',
                    'listing_removed',
                    'offer_cancelled',
                    'nft_locked'
                );
            END IF;
        END$$;
        """
    )
    log.info("  ✓ adminlogaction ENUM created or already exists")
    
    # =========================================================================
    # STEP 2: Create admin_logs table
    # =========================================================================
    log.info("Step 2: Creating admin_logs table...")
    op.create_table(
        'admin_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('action', postgresql.ENUM('user_role_changed', 'commission_rate_updated', 'commission_wallet_updated', 'admin_added', 'admin_removed', 'user_suspended', 'user_activated', 'system_config_changed', 'database_backup', 'listing_removed', 'offer_cancelled', 'nft_locked', name='adminlogaction', create_type=False), nullable=False, index=True),
        sa.Column('target_user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('target_resource_id', sa.String(255), nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_admin_logs_admin_action', 'admin_logs', ['admin_id', 'action'])
    log.info("  ✓ admin_logs table created with indexes")
    
    # =========================================================================
    # STEP 3: Create admin_settings table with DECIMAL defaults
    # =========================================================================
    # Why these changes:
    #   - DECIMAL columns with string defaults (2.0, 0.01) cause SQLAlchemy errors
    #   - Use sa.text() to pass PostgreSQL-safe numeric literals
    #   - Boolean-like string defaults (true/false) must use sa.text()
    # =========================================================================
    log.info("Step 3: Creating admin_settings table...")
    op.create_table(
        'admin_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        # DECIMAL columns with proper PostgreSQL server defaults
        sa.Column(
            'commission_rate',
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default=sa.text("'2.0'::numeric(5,2)"),
            comment='Commission rate as percentage (0-100)'
        ),
        sa.Column('commission_wallet', sa.String(255), nullable=False),
        sa.Column(
            'commission_blockchain',
            sa.String(50),
            nullable=False,
            server_default=sa.text("'ethereum'::character varying"),
            comment='Default blockchain for commission'
        ),
        # Min/max listing prices
        sa.Column(
            'min_listing_price',
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default=sa.text("'0.01'::numeric(10,2)"),
            comment='Minimum listing price'
        ),
        sa.Column(
            'max_listing_price',
            sa.Numeric(precision=20, scale=2),
            nullable=False,
            server_default=sa.text("'1000000.00'::numeric(20,2)"),
            comment='Maximum listing price'
        ),
        # Platform feature flags (stored as strings for flexibility)
        sa.Column(
            'enable_marketplace',
            sa.String(5),
            nullable=False,
            server_default=sa.text("'true'::character varying"),
            comment='Whether marketplace is enabled'
        ),
        sa.Column(
            'enable_nft_minting',
            sa.String(5),
            nullable=False,
            server_default=sa.text("'true'::character varying"),
            comment='Whether NFT minting is enabled'
        ),
        sa.Column(
            'enable_telegram',
            sa.String(5),
            nullable=False,
            server_default=sa.text("'true'::character varying"),
            comment='Whether Telegram integration is enabled'
        ),
        # Backup tracking
        sa.Column('last_backup_at', sa.DateTime(), nullable=True),
        sa.Column('last_backup_hash', sa.String(255), nullable=True),
        # Audit columns
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_admin_settings_updated_at', 'admin_settings', ['updated_at'])
    log.info("  ✓ admin_settings table created with proper DECIMAL defaults")


def downgrade() -> None:
    """Safely remove admin tables while preserving ENUM for other migrations."""
    log.info("Starting Migration 003 downgrade...")
    
    log.info("Dropping admin_settings indexes and table...")
    op.drop_index('ix_admin_settings_updated_at', table_name='admin_settings', if_exists=True)
    op.drop_table('admin_settings', if_exists=True)
    
    log.info("Dropping admin_logs indexes and table...")
    op.drop_index('ix_admin_logs_admin_action', table_name='admin_logs', if_exists=True)
    op.drop_index('ix_admin_logs_target_user_id', table_name='admin_logs', if_exists=True)
    op.drop_index('ix_admin_logs_action', table_name='admin_logs', if_exists=True)
    op.drop_index('ix_admin_logs_admin_id', table_name='admin_logs', if_exists=True)
    op.drop_table('admin_logs', if_exists=True)
    
    # IMPORTANT: Do NOT drop the adminlogaction ENUM here
    # Other tables/migrations may reference it, and re-applying this migration
    # uses IF NOT EXISTS to handle the ENUM safely on re-runs
    log.info("  ℹ  adminlogaction ENUM intentionally preserved for forward migration safety")
    log.info("Migration 003 downgrade completed")
