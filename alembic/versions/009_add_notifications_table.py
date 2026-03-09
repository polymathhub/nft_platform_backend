"""Add notifications table.

Revision ID: 009_add_notifications_table
Revises: 008_add_referral_system
Create Date: 2026-03-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '009_add_notifications_table'
down_revision = '008_add_referral_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notification type enum
    notification_type_enum = postgresql.ENUM(
        'nft_minted',
        'nft_sold',
        'nft_purchased',
        'nft_listed',
        'nft_offer_received',
        'nft_offer_accepted',
        'listing_sold',
        'offer_made',
        'offer_accepted',
        'payment_received',
        'payment_pending',
        'referral_earned',
        'account_verified',
        'account_warning',
        'password_changed',
        'info',
        'warning',
        'error',
        'success',
        name='notificationtype',
        create_type=True
    )
    notification_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('subject', sa.String(255), nullable=True),
        sa.Column('notification_type', notification_type_enum, nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('action_type', sa.String(50), nullable=True),
        sa.Column('extra_metadata', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('ix_notifications_notification_type', 'notifications', ['notification_type'])
    op.create_index('ix_notifications_expires_at', 'notifications', ['expires_at'])
    op.create_index(
        'idx_user_id_created_at',
        'notifications',
        ['user_id', 'created_at']
    )
    op.create_index(
        'idx_user_id_is_read',
        'notifications',
        ['user_id', 'is_read']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_user_id_is_read', table_name='notifications')
    op.drop_index('idx_user_id_created_at', table_name='notifications')
    op.drop_index('ix_notifications_expires_at', table_name='notifications')
    op.drop_index('ix_notifications_notification_type', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_is_read', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    
    # Drop table
    op.drop_table('notifications')
    
    # Drop enum
    notification_type_enum = postgresql.ENUM(
        'nft_minted',
        'nft_sold',
        'nft_purchased',
        'nft_listed',
        'nft_offer_received',
        'nft_offer_accepted',
        'listing_sold',
        'offer_made',
        'offer_accepted',
        'payment_received',
        'payment_pending',
        'referral_earned',
        'account_verified',
        'account_warning',
        'password_changed',
        'info',
        'warning',
        'error',
        'success',
        name='notificationtype'
    )
    notification_type_enum.drop(op.get_bind(), checkfirst=True)
