from alembic import op
import sqlalchemy as sa

revision = '013_add_wallet_address_to_users'
down_revision = '012_fix_alembic_version_column_size'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add wallet_address column to users table
    op.add_column(
        'users',
        sa.Column('wallet_address', sa.String(255), nullable=True)
    )
    # Create unique index on wallet_address
    op.create_index(
        'ix_users_wallet_address',
        'users',
        ['wallet_address'],
        unique=True
    )


def downgrade() -> None:
    # Drop the unique index
    op.drop_index('ix_users_wallet_address', table_name='users')
    # Drop the column
    op.drop_column('users', 'wallet_address')
