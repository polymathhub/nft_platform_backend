from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '007_add_activity_logs_table'
down_revision = '006_add_payments_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'activity_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('telegram_id', sa.String(50), nullable=True, index=True),
        sa.Column('telegram_username', sa.String(100), nullable=True, index=True),
        sa.Column('activity_type', sa.String(50), nullable=False, index=True),
        sa.Column('resource_type', sa.String(50), nullable=True, index=True),
        sa.Column('resource_id', sa.String(100), nullable=True, index=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('activity_metadata', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='success'),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_activity_user_timestamp', 'activity_logs', ['user_id', 'timestamp'])
    op.create_index('ix_activity_telegram_timestamp', 'activity_logs', ['telegram_id', 'timestamp'])
    op.create_index('ix_activity_type_timestamp', 'activity_logs', ['activity_type', 'timestamp'])
    op.create_index('ix_activity_resource', 'activity_logs', ['resource_type', 'resource_id'])


def downgrade() -> None:
    op.drop_index('ix_activity_resource', 'activity_logs')
    op.drop_index('ix_activity_type_timestamp', 'activity_logs')
    op.drop_index('ix_activity_telegram_timestamp', 'activity_logs')
    op.drop_index('ix_activity_user_timestamp', 'activity_logs')
    op.drop_table('activity_logs')
