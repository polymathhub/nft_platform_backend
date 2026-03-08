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
    bind = op.get_bind()

    # PostgreSQL: create ENUM type and add typed column
    if bind.dialect.name == 'postgresql':
        enum_type = postgresql.ENUM('admin', 'user', name='userrole', create_type=False)
        enum_type.create(bind, checkfirst=True)
        # Add user_role column safely if missing (Postgres supports IF NOT EXISTS)
        op.execute(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS user_role userrole DEFAULT 'user' NOT NULL;
            """
        )
    else:
        # For non-Postgres (sqlite/local dev), add a simple string column with default
        try:
            op.add_column('users', sa.Column('user_role', sa.String(), nullable=False, server_default='user'))
        except Exception:
            # If column already exists or add fails, continue gracefully
            pass

    # Create index if not exists (SQL works on SQLite and Postgres)
    try:
        op.execute("CREATE INDEX IF NOT EXISTS ix_users_user_role ON users (user_role);")
    except Exception:
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
