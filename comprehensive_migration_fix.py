import asyncio
import os
import sys
import subprocess
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
async def check_and_fix_alembic():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            print("\n" + "="*70)
            print("CHECKING ALEMBIC_VERSION TABLE STATUS")
            print("="*70)
            result = await conn.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1"))
            current = result.fetchone()
            if current:
                print(f"Current migration: {current[0]}")
            else:
                print("No migrations applied yet")
                return True
            row = result.fetchone()
            if row:
                col_name, max_length = row
                print(f"Current column: {col_name} VARCHAR({max_length})")
                if max_length and max_length < 128:
                    print(f"\n⚠️  Column too small! Expanding to VARCHAR(128)...")
                    print("✅ Column expanded successfully")
                    return True
                else:
                    print(f"✅ Column is already large enough ({max_length})")
                    return True
            else:
                print("ERROR: Could not find alembic_version.version_num column")
                return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()
async def main():
    python_exe = sys.executable
    print("\nStep 1: Checking and fixing alembic_version column size...")
    if not await check_and_fix_alembic():
        print("Failed to fix alembic_version column")
        return False
    print("\n" + "="*70)
    print("RUNNING ALEMBIC MIGRATIONS")
    print("="*70)
    project_root = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    cmd = [python_exe, "-m", "alembic", "upgrade", "head"]
    print(f"\nRunning: {' '.join(cmd)}")
    print(f"From directory: {project_root}")
    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        env=env,
        capture_output=False
    )
    if result.returncode == 0:
        print("\n✅ All migrations completed successfully!")
        return True
    else:
        print("\n❌ Migration failed")
        return False
if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
