from alembic import op
import sqlalchemy as sa

revision = '012_fix_alembic_version_column_size'
down_revision = '011_notifications_enum'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend the alembic_version table column to support longer version strings
    # This is needed when using UUID or longer revision identifiers
    op.alter_column(
        'alembic_version',
        'version_num',
        existing_type=sa.String(32),
        type_=sa.String(255),
    )


def downgrade() -> None:
    op.alter_column(
        'alembic_version',
        'version_num',
        existing_type=sa.String(255),
        type_=sa.String(32),
    )
