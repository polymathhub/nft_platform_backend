from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '009_add_notifications_table'
down_revision = '008_add_referral_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('subject', sa.String(255), nullable=True),
        sa.Column('notification_type', sa.String(50), nullable=False, index=True, server_default='info'),
        sa.Column('is_read', sa.Boolean(), nullable=False, index=True, server_default='false'),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('action_type', sa.String(50), nullable=True),
        sa.Column('extra_metadata', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_user_id_created_at', 'notifications', ['user_id', 'created_at'])
    op.create_index('idx_user_id_is_read', 'notifications', ['user_id', 'is_read'])


def downgrade() -> None:
    op.drop_index('idx_user_id_is_read', 'notifications')
    op.drop_index('idx_user_id_created_at', 'notifications')
    op.drop_table('notifications')
