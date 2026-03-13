"""Expand alembic_version.version_num column to support longer migration names.

Revision ID: 012_fix_alembic_version_column_size
Revises: 011_notifications_enum
Create Date: 2026-03-13 00:00:00.000000

This migration expands the alembic_version.version_num column from VARCHAR(32)
to VARCHAR(128) to support longer migration names. This is critical because
Alembic stores migration names as revision IDs, and our naming convention
(NNN_description_format) can exceed 32 characters.

Example:
  - Old limit: 32 chars - allows names like "010_add_ton_wallet_and_stars" (28 chars)
  - New limit: 128 chars - supports future longer descriptive names
  - Previous issue: "011_refactor_notifications_with_enum" (36 chars) now shortened to "011_notifications_enum" (22 chars)
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic
revision = '012_fix_alembic_version_column_size'
down_revision = '011_notifications_enum'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Expand the alembic_version.version_num column to VARCHAR(128)."""
    # Expand the version_num column to support longer migration names
    op.alter_column(
        'alembic_version',
        'version_num',
        existing_type=sa.String(length=32),
        type_=sa.String(length=128),
        existing_nullable=False
    )


def downgrade() -> None:
    """Revert the column size back to VARCHAR(32)."""
    op.alter_column(
        'alembic_version',
        'version_num',
        existing_type=sa.String(length=128),
        type_=sa.String(length=32),
        existing_nullable=False
    )
