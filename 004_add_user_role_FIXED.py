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
      log.warning("Sorry, this migration only speaks PostgreSQL.")
      return
    log.info("Adding user_role column to users table. It's ENUM-tastic!")
    op.execute(
    )
    log.info("  ✓ user_role column added or already exists with default='user'")
    log.info("Creating index on user_role. Because speed matters.")
    op.create_index(
        'ix_users_user_role',
        'users',
        ['user_role'],
        if_not_exists=True
    )
    log.info("  ✓ Index ix_users_user_role created")
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
    log.info("  ℹ  userrole ENUM intentionally preserved")
    log.info("Migration 004 downgrade completed")
