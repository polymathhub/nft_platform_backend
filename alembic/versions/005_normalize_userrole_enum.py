"""Normalize userrole enum labels to match Python Enum names.

Revision ID: 005_normalize_userrole_enum
Revises: 004_add_user_role
Create Date: 2026-02-14 00:00:00.000000

This migration renames existing enum labels ('user','admin') to
the uppercase labels ('USER','ADMIN') used by the `UserRole` Python enum.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '005_normalize_userrole_enum'
down_revision = '004_add_user_role'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Only run if the type exists and the lowercase values are present
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                -- rename 'user' -> 'USER' if present
                IF EXISTS (SELECT 1 FROM unnest(enum_range(NULL::userrole)) as v WHERE v::text = 'user')
                AND NOT EXISTS (SELECT 1 FROM unnest(enum_range(NULL::userrole)) as v WHERE v::text = 'USER') THEN
                    ALTER TYPE userrole RENAME VALUE 'user' TO 'USER';
                END IF;

                -- rename 'admin' -> 'ADMIN' if present
                IF EXISTS (SELECT 1 FROM unnest(enum_range(NULL::userrole)) as v WHERE v::text = 'admin')
                AND NOT EXISTS (SELECT 1 FROM unnest(enum_range(NULL::userrole)) as v WHERE v::text = 'ADMIN') THEN
                    ALTER TYPE userrole RENAME VALUE 'admin' TO 'ADMIN';
                END IF;
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    # Attempt to revert renames (only if uppercase values exist and lowercase don't)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                IF EXISTS (SELECT 1 FROM unnest(enum_range(NULL::userrole)) as v WHERE v = 'USER')
                AND NOT EXISTS (SELECT 1 FROM unnest(enum_range(NULL::userrole)) as v WHERE v = 'user') THEN
                    ALTER TYPE userrole RENAME VALUE 'USER' TO 'user';
                END IF;

                IF EXISTS (SELECT 1 FROM unnest(enum_range(NULL::userrole)) as v WHERE v = 'ADMIN')
                AND NOT EXISTS (SELECT 1 FROM unnest(enum_range(NULL::userrole)) as v WHERE v = 'admin') THEN
                    ALTER TYPE userrole RENAME VALUE 'ADMIN' TO 'admin';
                END IF;
            END IF;
        END$$;
        """
    )
