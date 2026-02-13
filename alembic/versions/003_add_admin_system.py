"""Add admin system tables and user role column.

Revision ID: 003_add_admin_system
Revises: 002_add_escrows_table
Create Date: 2026-02-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_admin_system'
down_revision = '002_add_escrows_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user_role column to users table
    op.add_column('users', sa.Column('user_role', sa.Enum('admin', 'user', name='userrole'), nullable=False, server_default='user'))
    op.create_index('ix_users_user_role', 'users', ['user_role'])
    
    # Create admin_logs table
    op.create_table(
        'admin_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.Enum('user_role_changed', 'commission_rate_updated', 'commission_wallet_updated', 'admin_added', 'admin_removed', 'user_suspended', 'user_activated', 'system_config_changed', 'database_backup', 'listing_removed', 'offer_cancelled', 'nft_locked', name='adminlogaction'), nullable=False),
        sa.Column('target_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_resource_id', sa.String(255), nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_admin_logs_admin_id', 'admin_logs', ['admin_id'])
    op.create_index('ix_admin_logs_action', 'admin_logs', ['action'])
    op.create_index('ix_admin_logs_target_user_id', 'admin_logs', ['target_user_id'])
    op.create_index('ix_admin_logs_created_at', 'admin_logs', ['created_at'])
    op.create_index('ix_admin_logs_admin_action', 'admin_logs', ['admin_id', 'action'])
    
    # Create admin_settings table
    op.create_table(
        'admin_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('commission_rate', sa.DECIMAL(5, 2), nullable=False, server_default='2.0'),
        sa.Column('commission_wallet', sa.String(255), nullable=False),
        sa.Column('commission_blockchain', sa.String(50), nullable=False, server_default='ethereum'),
        sa.Column('min_listing_price', sa.DECIMAL(10, 2), nullable=False, server_default='0.01'),
        sa.Column('max_listing_price', sa.DECIMAL(20, 2), nullable=False, server_default='1000000.00'),
        sa.Column('enable_marketplace', sa.String(5), nullable=False, server_default='true'),
        sa.Column('enable_nft_minting', sa.String(5), nullable=False, server_default='true'),
        sa.Column('enable_telegram', sa.String(5), nullable=False, server_default='true'),
        sa.Column('last_backup_at', sa.DateTime(), nullable=True),
        sa.Column('last_backup_hash', sa.String(255), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_admin_settings_updated_at', 'admin_settings', ['updated_at'])


def downgrade() -> None:
    op.drop_index('ix_admin_settings_updated_at', 'admin_settings')
    op.drop_table('admin_settings')
    
    op.drop_index('ix_admin_logs_admin_action', 'admin_logs')
    op.drop_index('ix_admin_logs_created_at', 'admin_logs')
    op.drop_index('ix_admin_logs_target_user_id', 'admin_logs')
    op.drop_index('ix_admin_logs_action', 'admin_logs')
    op.drop_index('ix_admin_logs_admin_id', 'admin_logs')
    op.drop_table('admin_logs')
    
    op.drop_index('ix_users_user_role', 'users')
    op.drop_column('users', 'user_role')
