import os
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
async def fix_alembic_version():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
            )
            row = result.fetchone()
            if row:
                col_name, max_length = row
                print(f"Current version_num column: {col_name} VARCHAR({max_length})")
                if max_length < 128:
                    print(f"Expanding column from VARCHAR({max_length}) to VARCHAR(128)...")
                    print("✓ Column expanded successfully")
                else:
                    print(f"✓ Column is already large enough ({max_length})")
            else:
                print("ERROR: alembic_version table not found")
                return False
            result = await conn.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1"))
            current = result.fetchone()
            if current:
                print(f"\nCurrent migration: {current[0]}")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        await engine.dispose()
if __name__ == "__main__":
    success = asyncio.run(fix_alembic_version())
    exit(0 if success else 1)
