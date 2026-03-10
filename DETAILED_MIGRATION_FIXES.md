# Detailed Migration Fixes - Line-by-Line Changes

## Migration 001: add_collection_rarity.py

### Problem
The `upgrade()` function had excessive indentation (16 spaces instead of 8).

### Root Cause
Manual indentation error during development - function body was over-indented.

### Before (BROKEN)
```python
def upgrade() -> None:
        bind = op.get_bind()
        
        # Create collections table if missing
        op.execute(
```

Notice: 8 spaces for function definition, then 16 spaces (double!) for the body.

### After (FIXED)
```python
def upgrade() -> None:
    """..."""
    bind = op.get_bind()
    
    # Create collections table if missing
    op.execute(
```

Now: 4-space indent for each level (proper Python style).

### Details of Change
- **Line 19**: Changed from 16 spaces to 8 spaces for `bind = op.get_bind()`
- **Lines 22-60**: All statements in upgrade() body adjusted from 16 to 8 spaces
- **Impact**: Function is now callable; Alembic can parse it correctly

### Why This Matters
Python requires consistent indentation. Alembic's internal parser validates this before running migrations. The double indentation caused:
- SyntaxError on import
- Alembic unable to register migration
- Migration directory shows as invalid

---

## Migration 004: add_user_role.py

### Problem
The `downgrade()` function was defined TWICE, with the second definition overwriting the first.

### Root Cause
Likely a merge conflict resolution error or duplicate copy-paste during development.

### Before (BROKEN) - Lines 94-132
```python
def downgrade() -> None:
    """Remove user_role column from users table."""
    
    log.info("Starting Migration 004 downgrade...")
    
    bind = op.get_bind()
    
    if bind.dialect.name != 'postgresql':
        log.warning("Downgrade skipped for non-PostgreSQL database")
        return
    
    # Drop index first
    log.info("Dropping index ix_users_user_role...")
    op.drop_index('ix_users_user_role', table_name='users', if_exists=True)
    
    # Drop column using IF EXISTS
    log.info("Removing user_role column...")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS user_role;")
    
    # userrole ENUM is intentionally preserved
    log.info("  ℹ  userrole ENUM intentionally preserved")
    log.info("Migration 004 downgrade completed")
        # best-effort index creation
        pass


def downgrade() -> None:
    """Rollback user_role column addition."""
    # These lines are wrong and cause the second definition to override first
    op.drop_index('ix_users_user_role', table_name='users')
    op.drop_column('users', 'user_role')
    
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        enum_type = postgresql.ENUM('admin', 'user', name='userrole')
        enum_type.drop(bind, checkfirst=True)
```

Issues:
1. Two `downgrade()` functions defined (line 94 AND line 119)
2. Second one is shorter and incorrect (doesn't use `if_exists=True`)
3. Final definition is what Alembic uses - causing logic to be lost from first version

### After (FIXED)
```python
def downgrade() -> None:
    """Remove user_role column from users table.
    
    Note: The userrole ENUM type is NOT dropped here because:
      - It was created in migration 003
      - Dropping must happen in 003's downgrade
      - Helps maintain referential integrity
    """
    
    log.info("Starting Migration 004 downgrade...")
    
    bind = op.get_bind()
    
    if bind.dialect.name != 'postgresql':
        log.warning("Downgrade skipped for non-PostgreSQL database")
        return
    
    # Drop index first
    log.info("Dropping index ix_users_user_role...")
    op.drop_index('ix_users_user_role', table_name='users', if_exists=True)
    
    # Drop column using IF EXISTS
    log.info("Removing user_role column...")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS user_role;")
    
    # userrole ENUM is intentionally preserved
    log.info("  ℹ  userrole ENUM intentionally preserved")
    log.info("Migration 004 downgrade completed")
```

### Details of Change
- **Deleted**: Lines 119 onward (entire second downgrade function)
- **Kept**: First downgrade function (corrected version with proper error handling)
- **Removed**: Orphaned code `# best-effort index creation` and `pass` statement

### Why This Matters
- Alembic scans for `def downgrade()` to register it
- When two definitions exist, Python uses the second one
- This caused downgrade to skip proper error handling and conditions
- Migration reversibility was broken

---

## Migration 010: add_ton_wallet_and_stars.py

### Problem
Server defaults for JSON/boolean columns used Python literals instead of PostgreSQL type-safe casting.

### Root Cause  
Mixing SQLAlchemy's `sa.literal()` (for Python objects) with PostgreSQL's type system. PostgreSQL requires explicit type casting for defaults.

### Before (BROKEN) - Multiple Locations

#### Issue 1: Boolean Column (is_primary)
```python
# BROKEN:
sa.Column(
    'is_primary',
    sa.Boolean(),
    nullable=False,
    server_default=sa.literal(True),  # ❌ Python bool literal
    comment='Whether this is the user\'s primary wallet'
),
```

Problem: `sa.literal(True)` generates SQL `true` without type info. PostgreSQL doesn't know it's a boolean.

#### Issue 2: String Status Column
```python
# BROKEN:
sa.Column(
    'status',
    sa.String(50),
    nullable=False,
    server_default=sa.literal('pending'),  # ❌ Python string literal
    index=True,
    comment='Wallet status: pending, connected, disconnected'
),
```

Problem: Similar issue - type context lost.

#### Issue 3: JSON Column (wallet_metadata)
```python
# BROKEN:
sa.Column(
    'wallet_metadata',
    sa.JSON(),
    nullable=False,
    server_default=sa.literal({}),  # ❌ Python dict literal - WORST
    comment='JSON metadata for wallet (public key, etc.)'
),
```

Problem: `sa.literal({})` tries to serialize Python dict to SQL, which:
- Fails on PostgreSQL side
- Creates `'{}'::unknown` type
- Breaks JSONB type checking
- Causes runtime CompileError

### After (FIXED) - Multiple Locations

#### Fix 1: Boolean Column
```python
# FIXED:
sa.Column(
    'is_primary',
    sa.Boolean(),
    nullable=False,
    server_default=sa.text("'true'::boolean"),  # ✓ Type-safe
    comment='Whether this is the user\'s primary wallet'
),
```

Explanation:
- `sa.text()` passes raw SQL to PostgreSQL
- `'true'::boolean` is PostgreSQL type casting syntax
- `something::type` means "cast something to type"
- PostgreSQL now knows the column type explicitly

#### Fix 2: String Status Column  
```python
# FIXED:
sa.Column(
    'status',
    sa.String(50),
    nullable=False,
    server_default=sa.text("'pending'::character varying"),  # ✓ Type-safe
    index=True,
    comment='Wallet status: pending, connected, disconnected'
),
```

Explanation:
- `'pending'::character varying` casts string to VARCHAR type
- Matches the Column type (String)
- PostgreSQL validates on creation

#### Fix 3: JSON Column
```python
# FIXED:
sa.Column(
    'wallet_metadata',
    sa.JSON(),
    nullable=False,
    server_default=sa.text("'{}'::jsonb"),  # ✓ Type-safe JSONB
    comment='JSON metadata for wallet (public key, etc.)'
),
```

Explanation:
- `'{}'::jsonb` casts empty JSON object to JSONB type
- JSONB is PostgreSQL's binary JSON (more efficient)
- Type mismatch with regular JSON still works but JSONB is preferred

### Applying to star_transactions Table
Same fixes applied to:
- **status** column at line ~338
- **tx_metadata** column at line ~360

### Why This Matters
- **CompileError**: SQLAlchemy can't generate valid SQL when types mismatch
- **Runtime Error**: PostgreSQL rejects the column definition at table creation
- **Type Safety**: Explicit casting ensures database integrity
- **Compatibility**: Async drivers (asyncpg) are stricter about types

---

## Migration 011: refactor_notifications_with_enum.py

### Problem #1: ForeignKeyConstraint in Wrong Location

#### The Issue Explained
Alembic has strict syntax rules for table constraints. The ForeignKeyConstraint MUST be a table-level argument, not a column-level one.

### Before (BROKEN) - Line 166
```python
sa.Column(
    'user_id',
    sa.Uuid(),  # ❌ ALSO WRONG TYPE
    sa.ForeignKeyConstraint(  # ❌ WRONG LOCATION - inside Column
        ['user_id'], ['users.id'], ondelete='CASCADE'
    ),
    nullable=False,
    index=True,
    comment='FK to users.id - Cascade deletes on user removal'
),
```

Error Generated:
```
AssertionError: isinstance(table, Table)
```

Why: Alembic's Column parser sees ForeignKeyConstraint as a second positional argument and gets confused. It expects `(name, type, [server_default], [constraints as keyword args])` not nested objects.

### After (FIXED) - Lines ~130-145 and separate ~250-260
```python
# Column definition (SIMPLE):
sa.Column(
    'user_id',
    postgresql.UUID(as_uuid=True),  # ✓ CORRECT TYPE
    nullable=False,
    index=True,
    comment='FK to users.id - Cascade deletes on user removal'
),

# ... much later in create_table, as SEPARATE argument:
sa.ForeignKeyConstraint(  # ✓ CORRECT LOCATION - table-level
    ['user_id'],
    ['users.id'],
    ondelete='CASCADE',
    name='fk_notifications_user_id'
),
```

### Problem #2: Using sa.Uuid() Instead of postgresql.UUID()

#### The Issue Explained
SQLAlchemy has two UUID implementations:
1. `sa.Uuid()` - Generic, database-agnostic
2. `postgresql.UUID(as_uuid=True)` - PostgreSQL-specific, optimized

### Before (BROKEN)
```python
sa.Column(
    'user_id',
    sa.Uuid(),  # ❌ Generic type, less efficient for Postgres
    nullable=False,
),
```

Problems:
- Doesn't leverage PostgreSQL's native UUID type
- Won't work with `gen_random_uuid()` function
- Missing UUID() capabilities specific to Postgres
- Asyncpg driver prefers explicit UUID type

### After (FIXED)
```python
sa.Column(
    'user_id',
    postgresql.UUID(as_uuid=True),  # ✓ Postgres-optimized
    nullable=False,
),
```

Benefits:
- Uses PostgreSQL's native UUID type
- Works with `gen_random_uuid()` defaults
- `as_uuid=True` converts to/from Python UUID objects
- Better performance and compatibility

### Problem #3: Server Defaults Without Type Casting

#### The Issue Explained
Similar to Migration 010 - boolean/string defaults need PostgreSQL type casting.

### Before (BROKEN) - Multiple Locations
```python
# Line: is_read column
sa.Column(
    'is_read',
    sa.Boolean(),
    nullable=False,
    server_default='false',  # ❌ String 'false', not typed
    index=True,
),

# read column  
sa.Column(
    'read',
    sa.Boolean(),
    nullable=False,
    server_default='false',  # ❌ String 'false', not typed
),
```

### After (FIXED)
```python
# is_read column
sa.Column(
    'is_read',
    sa.Boolean(),
    nullable=False,
    server_default=sa.text("'false'::boolean"),  # ✓ Type-safe
    index=True,
),

# read column
sa.Column(
    'read',
    sa.Boolean(),
    nullable=False,
    server_default=sa.text("'false'::boolean"),  # ✓ Type-safe
),
```

### Summary of All Changes in 011
1. **Line ~120**: Changed `sa.Uuid()` → `postgresql.UUID(as_uuid=True)`
2. **Lines ~150-170**: Moved ForeignKeyConstraint outside the Column definition
3. **Line ~173**: Changed `server_default='false'` → `sa.text("'false'::boolean")`
4. **Line ~188**: Changed `server_default='false'` → `sa.text("'false'::boolean")`
5. **Line ~250+**: Added ForeignKeyConstraint as separate table argument with name

---

## Quick Reference: Fix Patterns

### Pattern 1: JSON/JSONB Defaults
```python
# ❌ WRONG
server_default=sa.literal({})

# ✓ RIGHT
server_default=sa.text("'{}'::jsonb")
```

### Pattern 2: Boolean Defaults
```python
# ❌ WRONG
server_default=True
server_default='false'
server_default=sa.literal(False)

# ✓ RIGHT
server_default=sa.text("'true'::boolean")
server_default=sa.text("'false'::boolean")
```

### Pattern 3: String Defaults
```python
# ❌ WRONG
server_default='pending'
server_default=sa.literal('pending')

# ✓ RIGHT
server_default=sa.text("'pending'::character varying")
```

### Pattern 4: Numeric Defaults
```python
# ❌ WRONG
server_default=0.0
server_default=sa.literal(0)

# ✓ RIGHT
server_default=sa.text("'0.0'::numeric(10,2)")
server_default=sa.literal(0)  # Actually OK for pure numbers
```

### Pattern 5: Foreign Key Constraints
```python
# ❌ WRONG - Inside Column
sa.Column(
    'user_id', 
    postgresql.UUID(),
    sa.ForeignKeyConstraint(...)  # ❌ WRONG LOCATION
)

# ✓ RIGHT - Table level
op.create_table(
    'table_name',
    sa.Column('user_id', postgresql.UUID()),
    # ... other columns ...
    sa.ForeignKeyConstraint(  # ✓ CORRECT
        ['user_id'],
        ['users.id']
    )
)
```

### Pattern 6: UUID Columns
```python
# ❌ WRONG
sa.Column('id', sa.Uuid())

# ✓ RIGHT  
sa.Column('id', postgresql.UUID(as_uuid=True))
```

### Pattern 7: ENUM with Existing Type
```python
# ✓ CORRECT - Already exists
postgresql.ENUM(
    'value1', 'value2',
    name='enum_name',
    create_type=False,  # ✓ Don't create, reuse existing
)
```

---

## Testing Your Fixes

### 1. Syntax Validation
```bash
python -m py_compile alembic/versions/001_add_collection_rarity.py
python -m py_compile alembic/versions/004_add_user_role.py
python -m py_compile alembic/versions/010_add_ton_wallet_and_stars.py
python -m py_compile alembic/versions/011_refactor_notifications_with_enum.py
```

### 2. Alembic Syntax Check
```bash
alembic upgrade --sql head | head -100
```

### 3. Run Migrations
```bash
alembic upgrade head
```

### 4. Verify Database State
```bash
psql -d nft_platform -c "\\dt"  # List tables
psql -d nft_platform -c "\\d users"  # Describe users table
psql -d nft_platform -c "SELECT typname FROM pg_type WHERE typtype='e';"  # List enums
```

---

## If Issues Persist

### Issue: "function upgrade() not found"
**Cause**: Indentation error still present
**Fix**: Recount spaces - should be 4, 8, 12, etc.

### Issue: "duplicate downgrade"
**Cause**: Still have two downgrade functions
**Fix**: Delete the second one completely

### Issue: "unknown type xyz"  
**Cause**: Missing `create_type=False` in ENUM
**Fix**: Add to postgresql.ENUM constructor

### Issue: "cannot drop column with dependencies"
**Cause**: Dropping column before dropping constraint
**Fix**: Drop constraint first in downgrade

### Issue: "asyncpg driver error"
**Cause**: Using generic sa.Uuid() instead of postgresql.UUID()
**Fix**: Replace with postgresql.UUID(as_uuid=True)

---

## Files Created

The following corrected files are ready to use:

1. **001_add_collection_rarity_CORRECTED.py** 
   - Fix: Indentation 16→8 spaces in upgrade()
   
2. **004_add_user_role_CORRECTED.py**
   - Fix: Remove duplicate downgrade() function
   
3. **010_add_ton_wallet_and_stars_CORRECTED.py**
   - Fix: JSON/boolean defaults with sa.text() type casting
   
4. **011_refactor_notifications_with_enum_CORRECTED.py**
   - Fix 1: Move ForeignKeyConstraint outside Column
   - Fix 2: sa.Uuid() → postgresql.UUID(as_uuid=True)
   - Fix 3: Boolean defaults with sa.text() type casting

All other migrations (000, 002, 003, 005, 006, 007, 008, 009) are correct and need no changes.
