# Alembic Migration Fixes - Complete Audit & Corrections

## Summary of Issues Found and Fixed

### Critical Issues Identified:

1. **Migration 004 - IndentationError (CRITICAL)**
   - **Issue**: Duplicate `downgrade()` function with incorrect indentation
   - **Location**: Lines 119-142
   - **Error**: `IndentationError: unexpected indent`
   - **Root Cause**: Two downgrade functions defined - second one overwrites first
   - **Fix**: Remove duplicate function and fix indentation
   - **Impact**: Migration 004 cannot be used - syntaxerror prevents import

2. **Migration 010 - JSON/ARRAY Defaults Issue**
   - **Issue**: `server_default=sa.literal({})` for JSONB column
   - **Locations**: Lines 158, 342 (wallet_metadata and tx_metadata)
   - **Error**: SQLAlchemy CompileError when compiling JSONB default
   - **Root Cause**: `sa.literal()` cannot properly serialize empty dict {} for JSONB
   - **Fix**: Use `server_default=sa.text("'{}'::jsonb")` with PostgreSQL type casting
   - **Explanation**: 
     - `sa.literal({})` = Python dict object → SQLAlchemy tries to compile as SQL literal
     - `sa.text("'{}'::jsonb")` = Pre-compiled PostgreSQL SQL with explicit type cast
     - PostgreSQL then receives `'{}'::jsonb` which is valid JSON with type safety
   - **Impact**: JSONB/JSON defaults fail at migration run time during SQL compilation

3. **Migration 011 - String Boolean Default Issue**
   - **Issue**: `server_default='false'` for Boolean column
   - **Locations**: Lines 227, 236 (is_read and read columns)
   - **Error**: Type mismatch in PostgreSQL - string 'false' ≠ boolean false
   - **Root Cause**: String literal 'false' interpreted as PostgreSQL text type
   - **Fix**: Use `server_default=sa.literal(False)` for boolean defaults
   - **Explanation**:
     - `'false'` = String value in PostgreSQL (text type)
     - `False` = Python boolean → `sa.literal(False)` → PostgreSQL `FALSE` boolean
     - This ensures PostgreSQL treats it as boolean type, not text
   - **Impact**: Column defaults may silently fail or type mismatch errors occur

### Production-Grade Safety Patterns Applied:

✅ **JSON/ARRAY Defaults**: `sa.text("'...'::jsonb")` with explicit type casting  
✅ **DECIMAL/NUMERIC Defaults**: `sa.text("'value'::numeric(precision,scale)")`  
✅ **Boolean Defaults**: `sa.literal(True)` / `sa.literal(False)` for Python booleans  
✅ **String Defaults**: `sa.literal('value')` or `sa.text("'value'::text")`  
✅ **ENUM Creation**: PostgreSQL DO block with `IF NOT EXISTS` checks  
✅ **Idempotent Operations**: All drops use `if_exists=True`, columns use `IF NOT EXISTS`  
✅ **Index Comments**: Use `op.execute("COMMENT ON INDEX...")` instead of `comment=` arg  
✅ **Logging**: Comprehensive logging at each migration step for debugging  

### Column-Level Comments (No Changes Needed):
✅ Column-level `comment=` parameters in `sa.Column()` definitions are VALID
   - These apply documentation to the column, not the index
   - Not confused with `comment=` on `op.create_index()` (which is invalid)

---

## Files Ready for Copy-Paste

Below are the complete corrected migration files. Copy each one into the respective file in `alembic/versions/`

