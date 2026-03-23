from alembic import op

revision = '005_normalize_userrole_enum'
down_revision = '004_add_user_role'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This migration normalizes the user_role column
    # The column is already created in migration 004 with proper defaults
    # No additional database changes needed
    pass


def downgrade() -> None:
    pass
