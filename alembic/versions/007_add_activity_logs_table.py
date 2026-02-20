"""Add activity_logs table for audit trail and user activity tracking.

Revision ID: 007_add_activity_logs_table
Revises: 006_add_payments_table
Create Date: 2026-02-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_activity_logs_table'
down_revision = '006_add_payments_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create activity_logs table for audit trail and user activity tracking."""
    op.create_table(
        'activity_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('telegram_id', sa.String(50), nullable=True, index=True),
        sa.Column('telegram_username', sa.String(200), nullable=True, index=True),
        sa.Column('activity_type', sa.String(50), nullable=False, index=True),
        sa.Column('resource_type', sa.String(50), nullable=True, index=True),
        sa.Column('resource_id', sa.String(100), nullable=True, index=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('activity_metadata', sa.JSON(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for common queries
    op.create_index('ix_activity_logs_user_timestamp', 'activity_logs', ['user_id', 'timestamp'])
    op.create_index('ix_activity_logs_activity_type', 'activity_logs', ['activity_type', 'timestamp'])
    op.create_index('ix_activity_logs_resource', 'activity_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_activity_logs_telegram', 'activity_logs', ['telegram_id', 'timestamp'])


def downgrade() -> None:
    """Drop activity_logs table."""
    op.drop_index('ix_activity_logs_telegram')
    op.drop_index('ix_activity_logs_resource')
    op.drop_index('ix_activity_logs_activity_type')
    op.drop_index('ix_activity_logs_user_timestamp')
    op.drop_table('activity_logs')
