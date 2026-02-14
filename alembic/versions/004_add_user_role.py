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
    enum_type = postgresql.ENUM('admin', 'user', name='userrole', create_type=False)
    enum_type.create(op.get_bind(), checkfirst=True)
    
    # Add user_role column with default value USER
    op.add_column(
        'users',
        sa.Column(
            'user_role',
            sa.Enum('admin', 'user', name='userrole'),
            nullable=False,
            server_default='user'
        )
    )
    
    # Create index on user_role column
    op.create_index('ix_users_user_role', 'users', ['user_role'])


def downgrade() -> None:
    """Rollback user_role column addition."""
    # Drop the index
    op.drop_index('ix_users_user_role', table_name='users')
    
    # Drop the column
    op.drop_column('users', 'user_role')
    
    # Drop the enum type
    enum_type = postgresql.ENUM('admin', 'user', name='userrole')
    enum_type.drop(op.get_bind(), checkfirst=True)
