#!/usr/bin/env python
"""Test database connection and run migration"""
import sys
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_connection():
    from sqlalchemy.ext.asyncio import create_async_engine
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    print(f"Testing connection to: {db_url[:50]}...")
    
    try:
        engine = create_async_engine(db_url, echo=True)
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print("✓ Connection successful!")
            return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    try:
        success = asyncio.run(test_connection())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
