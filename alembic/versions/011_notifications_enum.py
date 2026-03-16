from alembic import op
import sqlalchemy as sa

revision = '011_notifications_enum'
down_revision = '010_add_ton_wallet_and_stars'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This migration is a placeholder for notification type enum normalization
    # The notification_type column in notifications table is already String type
    # No database changes needed at this moment
    pass


def downgrade() -> None:
    pass
