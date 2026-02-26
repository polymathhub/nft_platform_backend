"""Add referral system tables and extend User model.

Revision ID: 008_add_referral_system
Revises: 007_add_activity_logs_table
Create Date: 2026-02-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_referral_system'
down_revision = '007_add_activity_logs_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add referral system support to users and create referral tables."""
    
    # Add columns to users table (creator fields)
    op.add_column('users', sa.Column('is_creator', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('creator_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('creator_bio', sa.String(1000), nullable=True))
    op.add_column('users', sa.Column('creator_avatar_url', sa.String(500), nullable=True))
    
    # Add columns to users table (referral fields)
    op.add_column('users', sa.Column('referral_code', sa.String(50), nullable=True, unique=True))
    op.add_column('users', sa.Column('referred_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('users', sa.Column('referral_locked_at', sa.DateTime(), nullable=True))
    
    # Add columns to users table (payment fields)
    op.add_column('users', sa.Column('stars_balance', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('users', sa.Column('total_stars_earned', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('users', sa.Column('total_stars_spent', sa.Float(), nullable=False, server_default='0.0'))
    
    # Create indexes on users table for new columns
    op.create_index('ix_users_referral_code', 'users', ['referral_code'])
    op.create_index('ix_users_is_creator', 'users', ['is_creator'])
    op.create_index('ix_users_referred_by', 'users', ['referred_by_id'])
    
    # Add foreign key constraint for referred_by_id
    op.create_foreign_key(
        'fk_users_referred_by_id',
        'users', 'users',
        ['referred_by_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create referrals table
    op.create_table(
        'referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('referrer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('referred_user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('referral_code', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, index=True, server_default='active'),
        sa.Column('lifetime_earnings', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('referred_purchase_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('referred_purchase_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('first_purchase_at', sa.DateTime(), nullable=True),
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['referrer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['referred_user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes on referrals table
    op.create_index('ix_referrals_referrer_status', 'referrals', ['referrer_id', 'status'])
    op.create_index('ix_referrals_code_status', 'referrals', ['referral_code', 'status'])
    
    # Create referral_commissions table
    op.create_table(
        'referral_commissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('referral_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('commission_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('commission_rate', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('transaction_amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, index=True, server_default='pending'),
        sa.Column('earned_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['referral_id'], ['referrals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['payments.id'], ondelete='CASCADE'),
    )
    
    # Create indexes on referral_commissions table
    op.create_index('ix_referral_commissions_referral_status', 'referral_commissions', ['referral_id', 'status'])


def downgrade() -> None:
    """Revert referral system changes."""
    
    # Drop tables in reverse order
    op.drop_table('referral_commissions')
    op.drop_table('referrals')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_users_referred_by_id', 'users', type_='foreignkey')
    
    # Drop indexes from users table
    op.drop_index('ix_users_referred_by')
    op.drop_index('ix_users_is_creator')
    op.drop_index('ix_users_referral_code')
    
    # Drop columns from users table
    op.drop_column('users', 'total_stars_spent')
    op.drop_column('users', 'total_stars_earned')
    op.drop_column('users', 'stars_balance')
    op.drop_column('users', 'referral_locked_at')
    op.drop_column('users', 'referred_by_id')
    op.drop_column('users', 'referral_code')
    op.drop_column('users', 'creator_avatar_url')
    op.drop_column('users', 'creator_bio')
    op.drop_column('users', 'creator_name')
    op.drop_column('users', 'is_creator')
