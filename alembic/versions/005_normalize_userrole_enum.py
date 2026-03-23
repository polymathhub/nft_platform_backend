from alembic import op
revision = '005_normalize_userrole_enum'
down_revision = '004_add_user_role'
branch_labels = None
depends_on = None
def upgrade() -> None:
    # This is a placeholder migration for future userrole ENUM normalization.
    # The userrole ENUM is already created in migration 004.
    # No additional changes needed at this time.
    pass
def downgrade() -> None:
    pass
