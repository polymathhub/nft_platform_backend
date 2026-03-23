import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
log = logging.getLogger(__name__)
revision = '004_add_user_role'
down_revision = '003_add_admin_system'
branch_labels = None
depends_on = None
def upgrade() -> None:
    log.info("Starting Migration 004: Add user_role column to users table")
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        log.warning(
            "Migration 004 is optimized for PostgreSQL. "
            "For other databases, manual adjustment required."
        )
        return
    log.info("Step 1: Creating userrole ENUM type...")
    # Create the ENUM type explicitly before using it
    op.execute(
        "CREATE TYPE userrole AS ENUM ('admin', 'user') IF NOT EXISTS"
    )
    log.info("Step 2: Adding user_role column to users table...")
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS user_role userrole DEFAULT 'user' NOT NULL"
    )
    log.info("  user_role column added or already exists with default='user'")
    log.info("Step 2: Creating index on user_role...")
    op.create_index(
        'ix_users_user_role',
        'users',
        ['user_role'],
        if_not_exists=True
    )
    log.info("  Index ix_users_user_role created")
    log.info("Migration 004 upgrade completed successfully")
def downgrade() -> None:
    log.info("Starting Migration 004 downgrade...")
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        log.warning("Downgrade skipped for non-PostgreSQL database")
        return
    log.info("Dropping index ix_users_user_role...")
    op.drop_index('ix_users_user_role', table_name='users', if_exists=True)
    log.info("Removing user_role column...")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS user_role;")
    log.info("Dropping userrole ENUM type...")
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")
    log.info("Migration 004 downgrade completed")
