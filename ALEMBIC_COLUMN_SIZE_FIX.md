# Fix for Alembic Version Column Size Error

## Problem Summary

**Error:** `StringDataRightTruncationError: value too long for type character varying(32)`

**Cause:** The migration name `'011_refactor_notifications_with_enum'` is 36 characters long, but the `alembic_version.version_num` column is only VARCHAR(32), causing it to exceed the limit.

```
Migration name length: 36 chars
Column size limit: 32 chars
⚠️ EXCEEDS LIMIT BY 4 CHARACTERS
```

## Solution

The issue has been fixed with a new migration (`012_fix_alembic_version_column_size`) that expands the column to VARCHAR(128).

### Quick Fix Steps

#### Option 1: Automatic Fix (Recommended)

```powershell
# Activate virtual environment (if not already)
.\.venv\Scripts\Activate.ps1

# Run the comprehensive fix script
python comprehensive_migration_fix.py
```

This script will:
1. ✅ Check the current migration state
2. ✅ Expand the `alembic_version.version_num` column to VARCHAR(128)
3. ✅ Run all pending migrations (including the new migration 012)
4. ✅ Report success/failure

#### Option 2: Manual Fix

If the automatic fix doesn't work, do this manually:

```powershell
# 1. Connect to PostgreSQL database
psql -U postgres -d nft_platform -c "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE varchar(128);"

# 2. Run migrations
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

### What Changed

#### New Migration: `012_fix_alembic_version_column_size`

- **Revision ID:** `012_fix_alembic_version_column_size`
- **Previous migration:** `011_refactor_notifications_with_enum`
- **Action:** Expands `alembic_version.version_num` from VARCHAR(32) to VARCHAR(128)
- **Reason:** Supports longer migration names while maintaining backward compatibility

### Testing the Fix

After running the fix, verify it worked:

```powershell
# Check if migrations completed
python -c "from sqlalchemy import create_engine, text; engine = create_engine('postgresql://user:pass@localhost/nft_platform'); 
with engine.connect() as conn: 
    result = conn.execute(text('SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 3'));
    for row in result: print(row[0])"
```

Expected output showing the last 3 migrations:
```
012_fix_alembic_version_column_size
011_refactor_notifications_with_enum
010_add_ton_wallet_and_stars
```

### Application Startup

The application's startup process (`app/utils/startup.py`) will automatically handle this:

1. On startup, it runs `alembic upgrade head`
2. This will now succeed because:
   - The column is expanded (migration 012)
   - Migration 011 can now be recorded with its full name
   - Future migrations with longer names are supported

### Prevention

For future migrations, follow these naming conventions:
- Keep revision IDs under 100 characters
- Use descriptive but concise names
- Pattern: `NNN_short_description`

### Files Modified

1. **New migration file:**
   - `alembic/versions/012_fix_alembic_version_column_size.py` - Expands the column

2. **New fix scripts:**
   - `comprehensive_migration_fix.py` - Automated fix script
   - `fix_alembic_version_column.py` - Simple check/fix utility

### Rollback (If Needed)

If something goes wrong, Alembic can downgrade:

```powershell
# Downgrade to previous migration
alembic downgrade 011_refactor_notifications_with_enum

# Then re-run
alembic upgrade head
```

## Additional Context

### Why This Happened

1. Alembic stores migration revision IDs in the `alembic_version` table
2. The initial schema (migration 000) created this table with VARCHAR(32)
3. When migration names exceed 32 characters, the INSERT/UPDATE fails
4. Standard Alembic default is VARCHAR(32), which is too restrictive for descriptive names

### Design Decisions

The new migration 012:
- ✅ Uses standard Alembic ALTER COLUMN syntax
- ✅ Is idempotent (safe to run multiple times)
- ✅ Maintains backward compatibility
- ✅ Allows future longer migration names
- ✅ Includes proper upgrade/downgrade functions

### Troubleshooting

If issues persist:

1. **Database connection problems:**
   ```powershell
   # Test database connection
   python test_connection.py
   ```

2. **Check migration status:**
   ```powershell
   alembic current
   alembic history
   ```

3. **View Alembic logs:**
   - Check the migration files in `alembic/versions/`
   - Run with verbose output: `alembic upgrade head --verbose`

## Next Steps

1. Run the comprehensive fix script
2. Verify migrations completed successfully
3. Start the application normally
4. Check logs for any remaining errors

If you encounter any issues:
- Check `alembic history` to see migration progression
- Review logs in the terminal output
- Ensure DATABASE_URL environment variable is set correctly
