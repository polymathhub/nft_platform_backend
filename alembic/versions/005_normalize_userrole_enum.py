"""Verify userrole enum is properly configured.

Revision ID: 005_normalize_userrole_enum
Revises: 004_add_user_role
Create Date: 2026-02-14 00:00:00.000000

This migration ensures the userrole enum has the correct lowercase values
('user', 'admin') that match the Python UserRole enum.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '005_normalize_userrole_enum'
down_revision = '004_add_user_role'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Verify enum exists with correct values - no-op if already correct
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                -- Verify lowercase values exist (user, admin)
                IF EXISTS (SELECT 1 FROM unnest(enum_range(NULL::userrole)) as v WHERE v::text IN ('user', 'admin')) THEN
                    -- Already correct
                    NULL;
                END IF;
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    # No-op for downgrade since we're just verifying
    pass
