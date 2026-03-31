"""Fix UserRole enum case mismatch - use lowercase values

Revision ID: 019_fix_userrole_enum_case
Revises: 018_add_referral_and_stars_columns_to_users
Create Date: 2026-03-31 14:15:00.000000

The UserRole enum in the model defines values as lowercase ('user', 'admin'),
but SQLAlchemy was trying to insert uppercase Python enum names ('USER', 'ADMIN').
This migration fixes the mismatch by recreating the enum type properly.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '019_fix_userrole_enum_case'
down_revision = '018_add_referral_and_stars_columns_to_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing constraint on user_role column
    op.execute('ALTER TABLE users ALTER COLUMN user_role DROP DEFAULT')
    
    # Drop the old enum type
    op.execute('DROP TYPE IF EXISTS userrole CASCADE')
    
    # Create new enum type with lowercase values
    op.execute("CREATE TYPE userrole AS ENUM ('user', 'admin')")
    
    # Add column back with proper type
    op.execute("ALTER TABLE users ADD COLUMN user_role_new userrole DEFAULT 'user' NOT NULL")
    
    # Copy data from old column if it exists (convert to lowercase)
    op.execute("""
        UPDATE users 
        SET user_role_new = LOWER(CAST(user_role AS text))::userrole
        WHERE user_role IS NOT NULL
    """)
    
    # Drop old column and rename new one
    op.execute('ALTER TABLE users DROP COLUMN user_role')
    op.execute('ALTER TABLE users RENAME COLUMN user_role_new TO user_role')


def downgrade() -> None:
    # Revert to previous state
    op.execute('DROP TYPE IF EXISTS userrole CASCADE')
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'user')")
    op.execute("ALTER TABLE users ADD COLUMN user_role userrole DEFAULT 'user' NOT NULL")
