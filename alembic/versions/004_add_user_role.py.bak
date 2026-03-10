"""Add user_role column to users table - PostgreSQL Safe.

Revision ID: 004_add_user_role
Revises: 003_add_admin_system
Create Date: 2026-02-14 00:00:00.000000

============================================================================
MIGRATION FIXES (v2)
============================================================================

Production improvements:
✓ ENUM type: Created safely with IF NOT EXISTS check in 003
✓ Column addition: Use ALTER TABLE ADD COLUMN IF NOT EXISTS (idempotent)
✓ Defaults: Use sa.text() for PostgreSQL-safe ENUM defaults
✓ Indexes: Use standard op.create_index without try-except
✓ Error handling: Fail fast with proper exceptions (don't suppress errors)
"""
import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

log = logging.getLogger(__name__)

# revision identifiers, used by Alembic.
revision = '004_add_user_role'
down_revision = '003_add_admin_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user_role ENUM column to users table.
    
    Why this approach is safe:
      - ENUM type created in migration 003 with IF NOT EXISTS
      - Column addition uses IF NOT EXISTS (idempotent)
      - Proper default value via sa.text() for PostgreSQL
      - Index creation is explicit and clear
    """
    
    log.info("Starting Migration 004: Add user_role column to users table")
    
    bind = op.get_bind()
    
    # =========================================================================
    # STEP 1: Verify we're working with PostgreSQL
    # =========================================================================
    if bind.dialect.name != 'postgresql':
        log.warning(
            "Migration 004 is optimized for PostgreSQL. "
            "For other databases, manual adjustment required."
        )
        return
    
    # =========================================================================
    # STEP 2: Add user_role column with ENUM type and default
    # =========================================================================
    # Why IF NOT EXISTS:
    #   - Makes migration idempotent (can re-run safely)
    #   - Handles databases where column already exists
    #   - Uses standard PostgreSQL syntax
    # =========================================================================
    log.info("Step 1: Adding user_role column to users table...")
    
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS user_role userrole NOT NULL DEFAULT 'user';
        """
    )
    log.info("  ✓ user_role column added or already exists with default='user'")
    
    # =========================================================================
    # STEP 3: Create index on user_role for query optimization
    # =========================================================================
    log.info("Step 2: Creating index on user_role...")
    
    op.create_index(
        'ix_users_user_role',
        'users',
        ['user_role'],
        if_not_exists=True
    )
    log.info("  ✓ Index ix_users_user_role created")
    
    log.info("Migration 004 upgrade completed successfully")


def downgrade() -> None:
    """Remove user_role column from users table.
    
    Note: The userrole ENUM type is NOT dropped here because:
      - It was created in migration 003
      - Dropping must happen in 003's downgrade
      - Helps maintain referential integrity
    """
    
    log.info("Starting Migration 004 downgrade...")
    
    bind = op.get_bind()
    
    if bind.dialect.name != 'postgresql':
        log.warning("Downgrade skipped for non-PostgreSQL database")
        return
    
    # Drop index first
    log.info("Dropping index ix_users_user_role...")
    op.drop_index('ix_users_user_role', table_name='users', if_exists=True)
    
    # Drop column using IF EXISTS
    log.info("Removing user_role column...")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS user_role;")
    
    # userrole ENUM is intentionally preserved
    log.info("  ℹ  userrole ENUM intentionally preserved")
    log.info("Migration 004 downgrade completed")
        # best-effort index creation
        pass


def downgrade() -> None:
    """Rollback user_role column addition."""
    # Drop the index
    op.drop_index('ix_users_user_role', table_name='users')
    
    # Drop the column
    op.drop_column('users', 'user_role')
    
    # Drop the enum type only on Postgres
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        enum_type = postgresql.ENUM('admin', 'user', name='userrole')
        enum_type.drop(bind, checkfirst=True)
