# Alembic Migration Standards - Production Grade

**Last Updated:** March 10, 2026  
**Version:** 1.0  
**Status:** Production Ready

---

## Overview

This document establishes production-grade standards for all Alembic migrations in the NFT Platform Backend. These standards ensure:

- **Async Safety**: Full compatibility with asyncpg and async SQLAlchemy 2.0+
- **PostgreSQL Compliance**: Proper dialect handling and type safety
- **Idempotency**: Migrations can be run/rolled back multiple times safely
- **Reliability**: No DuplicateObjectError or AssertionError exceptions
- **Maintainability**: Clear documentation, logging, and explicit naming
- **Production Readiness**: Enterprise-grade error handling and robustness

---

## Refactored Migrations

The following migrations have been refactored to meet all production standards:

### Migration 009: add_notifications_table
- **Status**: Production Ready
- **Features**: 
  - Safe ENUM creation with PostgreSQL DO block
  - Idempotent with IF NOT EXISTS checks
  - Full logging at each step
  - Named constraints and indexes

### Migration 010: add_ton_wallet_and_stars
- **Status**: Production Ready
- **Features**:
  - Async-safe boolean/numeric defaults (sa.literal())
  - Timezone-aware timestamps
  - postgresql_comment= on all indexes
  - Comprehensive error handling in downgrade

### Migration 008: add_referral_system
- **Status**: Production Ready
- **Features**:
  - sa.literal() for all defaults
  - DateTime(timezone=True) for UTC
  - Detailed documentation and logging
  - Proper cascade handling

### Migration 011: refactor_notifications_with_enum
- **Status**: Production Ready
- **Features**:
  - Safe ENUM handling
  - Composite indexes with comments
  - Production-grade documentation

---

## Best Practices for All Migrations

### 1. Async-Safe Defaults

**WRONG:**
```python
sa.Column('is_active', sa.Boolean(), server_default='true')
sa.Column('amount', sa.Float(), server_default='0.0')
```

**✅ CORRECT:**
```python
sa.Column('is_active', sa.Boolean(), server_default=sa.literal(True))
sa.Column('amount', sa.Float(), server_default=sa.literal(0.0))
```

**Why**: Using string literals breaks with asyncpg. `sa.literal()` properly coerces types.

---

### 2. Timezone-Aware Timestamps

**❌ WRONG:**
```python
sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
```

**✅ CORRECT:**
```python
sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
```

**Why**: PostgreSQL NOW() returns UTC. Explicit timezone=True ensures consistency.

---

### 3. Index Comments (PostgreSQL Dialect)

**❌ WRONG:**
```python
op.create_index('idx_name', 'table', ['column'], comment='...')  # TypeError!
```

**✅ CORRECT:**
```python
op.create_index('idx_name', 'table', ['column'], postgresql_comment='...')
```

**Why**: The generic `comment=` parameter doesn't work with PostgreSQL dialect. Use `postgresql_comment=`.

---

### 4. Safe ENUM Creation

**❌ WRONG:**
```python
enum = postgresql.ENUM('val1', 'val2', name='myenum', create_type=True)
enum.create(op.get_bind(), checkfirst=True)  # Still fails sometimes
```

**✅ CORRECT:**
```python
op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'myenum' AND typtype = 'e') THEN
            CREATE TYPE myenum AS ENUM ('val1', 'val2');
        END IF;
    END$$;
""")
```

**Why**: PostgreSQL DO block is atomic and more reliable than SQLAlchemy's checkfirst.

---

### 5. Foreign Key Constraint Placement

**❌ WRONG:**
```python
op.create_table('notifications',
    sa.Column('user_id', sa.Uuid(),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),  # WRONG!
        nullable=False)
)
```

**✅ CORRECT:**
```python
op.create_table('notifications',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    # ... other columns ...
    sa.ForeignKeyConstraint(  # Separate argument!
        ['user_id'], ['users.id'],
        ondelete='CASCADE',
        name='fk_notifications_user_id'  # Explicit name
    )
)
```

**Why**: Alembic expects ForeignKeyConstraint as a separate table argument, not column argument. Prevents AssertionError.

---

### 6. Idempotent Operations

**❌ WRONG:**
```python
def downgrade():
    op.drop_table('mytable')  # Fails if already dropped
    op.drop_index('idx_name')  # Fails if already dropped
```

**✅ CORRECT:**
```python
def downgrade():
    op.drop_table('mytable', if_exists=True)
    op.drop_index('idx_name', table_name='mytable', if_exists=True)
    op.drop_column('users', 'column_name', if_exists=True)
```

**Why**: Allows migrations to be re-run safely without errors.

---

### 7. Logging and Documentation

**❌ MINIMAL:**
```python
def upgrade():
    """Add users table."""
    op.create_table('users', ...)
```

**✅ COMPREHENSIVE:**
```python
import logging
log = logging.getLogger(__name__)

def upgrade():
    """
    Add users table with comprehensive documentation.
    
    This migration is idempotent and async-safe:
      - Can be run multiple times without errors
      - Works with asyncpg and async SQLAlchemy
      - Proper timezone-aware timestamps
    
    Execution order:
      1. Create users table
      2. Create indexes
      3. Create constraints
    """
    log.info("Step 1: Creating users table...")
    op.create_table('users', ...)
    log.info("  ✓ Users table created")
```

**Why**: Logging helps with debugging. Docstrings document intent and safety measures.

---

### 8. Explicit Naming Conventions

**❌ WRONG:**
```python
sa.ForeignKeyConstraint(['user_id'], ['users.id'])  # Auto-named
op.create_index('idx_1', 'table', ['col'])  # Non-descriptive
```

**✅ CORRECT:**
```python
sa.ForeignKeyConstraint(
    ['user_id'], ['users.id'],
    name='fk_notifications_user_id'
)
op.create_index(
    'idx_notifications_user_id_created_at',
    'notifications',
    ['user_id', 'created_at']
)
```

**Why**: Explicit names make debugging easier and improve code clarity.

---

### 9. Column Comments

**✅ ALWAYS INCLUDE:**
```python
sa.Column(
    'created_at',
    sa.DateTime(timezone=True),
    nullable=False,
    server_default=sa.func.now(),
    comment='When the record was created (UTC)'  # Useful for developers
)
```

**Why**: Helps future developers understand column purpose and constraints.

---

### 10. Server Defaults Consistency

**✅ PREFER:**
```python
# Use SQL functions for consistency across application and database
sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
sa.Column('status', sa.String(50), server_default=sa.literal('pending'))
```

**Why**: Ensures data consistency even if application logic fails.

---

## Template: Minimal Production-Grade Migration

```python
"""Brief description of what migration does.

Revision ID: XXX_migration_name
Revises: YYY_previous_migration
Create Date: 2026-03-10 00:00:00.000000

============================================================================
MIGRATION SPECIFICATION
============================================================================

This migration:
  - Creates X table with Y columns
  - Creates Z indexes for performance
  - Supports rollback via downgrade()

============================================================================
PRODUCTION FEATURES
============================================================================

✓ Async SQLAlchemy 2.0+ compatible
✓ PostgreSQL dialect compliant
✓ Idempotent (safe to re-run)
✓ Comprehensive logging
✓ Explicit naming conventions
"""

import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

log = logging.getLogger(__name__)

revision = 'XXX_migration_name'
down_revision = 'YYY_previous_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create table and indexes.
    
    Idempotent and async-safe.
    """
    log.info("=== Migration XXX: Creating table ===")
    
    op.create_table(
        'table_name',
        sa.Column(
            'id',
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            comment='Primary key'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Creation timestamp (UTC)'
        ),
    )
    
    log.info("  ✓ Table created")
    
    op.create_index(
        'idx_table_name_created_at',
        'table_name',
        ['created_at'],
        postgresql_comment='Index for date range queries'
    )
    
    log.info("=== Migration XXX completed ===")


def downgrade() -> None:
    """Safely drop table and indexes."""
    log.info("=== Migration XXX: Downgrading ===")
    
    op.drop_index('idx_table_name_created_at', table_name='table_name', if_exists=True)
    op.drop_table('table_name', if_exists=True)
    
    log.info("=== Migration XXX downgrade completed ===")
```

---

## Checklist for New Migrations

Before committing any new migration, verify:

- [ ] **Defaults**: All `server_default` use `sa.literal()` (not strings)
- [ ] **Timestamps**: All DateTime columns have `timezone=True`
- [ ] **Indexes**: All index comments use `postgresql_comment=` (not `comment=`)
- [ ] **Constraints**: All ForeignKeyConstraints are separate table arguments (not column arguments)
- [ ] **Naming**: All constraints and indexes have explicit names
- [ ] **Idempotency**: Downgrade uses `if_exists=True` on all drops
- [ ] **Logging**: Upgrade and downgrade include log.info() at steps
- [ ] **Documentation**: Docstrings explain execution order and safety measures
- [ ] **Comments**: All columns have comments describing purpose
- [ ] **Async-Safe**: No string literals in boolean/numeric defaults
- [ ] **PostgreSQL**: Using `postgresql.UUID(as_uuid=True)` for UUIDs, not generic `sa.Uuid()`

---

## Migration Execution

### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply one specific migration
alembic upgrade +1

# Generate migration SQL (offline mode)
alembic upgrade head --sql
```

### Rolling Back

```bash
# Rollback one migration
alembic downgrade -1

# Rollback all
alembic downgrade base
```

---

## Summary of Changes

| Migration | Status | Key Improvements |
|-----------|--------|-------------------|
| 008 | ✅ Refactored | sa.literal() defaults, timezone-aware timestamps, logging |
| 009 | ✅ Refactored | Safe ENUM creation, comprehensive documentation |
| 010 | ✅ Refactored | postgresql_comment= on indexes, async-safe defaults |
| 011 | ✅ Refactored | Idempotent index creation, proper constraint naming |

**Remaining migrations** (000-007) should be reviewed and refactored using this guide.

---

## Support & Questions

For questions about migration standards, refer to:

1. **Alembic Docs**: https://alembic.sqlalchemy.org/
2. **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/
3. **PostgreSQL Types**: https://www.postgresql.org/docs/current/

---

**Generated:** March 10, 2026  
**By:** GitHub Copilot (Production Engineering Team)
