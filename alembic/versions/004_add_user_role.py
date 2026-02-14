"""Add user_role column to users table."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '004_add_user_role'
down_revision = '003_add_admin_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user_role column to users table."""
    # Create the enum type if it doesn't exist
    bind = op.get_bind()
    enum_type = postgresql.ENUM('admin', 'user', name='userrole', create_type=False)
    enum_type.create(bind, checkfirst=True)

    # Add user_role column safely if missing
    bind.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS user_role userrole DEFAULT 'user' NOT NULL;
        """
    )

    # Create index if not exists
    bind.execute(
        "CREATE INDEX IF NOT EXISTS ix_users_user_role ON users (user_role);"
    )


def downgrade() -> None:
    """Rollback user_role column addition."""
    # Drop the index
    op.drop_index('ix_users_user_role', table_name='users')
    
    # Drop the column
    op.drop_column('users', 'user_role')
    
    # Drop the enum type
    enum_type = postgresql.ENUM('admin', 'user', name='userrole')
    enum_type.drop(op.get_bind(), checkfirst=True)
