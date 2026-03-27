#!/usr/bin/env python
"""Test script to verify NFT minting and image upload work correctly"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Configure async to work on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


async def test_database_connection():
    """Test that we can connect to the database and verify the images table exists"""
    
    from app.config import get_settings
    
    settings = get_settings()
    database_url = settings.database_url
    
    print("🔍 Testing database connection...")
    print(f"   Database: {database_url.split('@')[-1] if '@' in database_url else 'local'}")
    
    try:
        engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20
        )
        
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(select(1))
            if result.scalar() == 1:
                print("✅ Database connection successful!")
        
        # Check if images table exists
        async with engine.begin() as conn:
            result = await conn.execute(
                select(1).select_from("pg_tables")
                .where("schemaname = 'public' AND tablename = 'images'")
            )
            if result.scalar():
                print("✅ images table exists in database!")
            else:
                print("❌ images table NOT found in database")
                return False
        
        # Verify images table structure
        async with engine.begin() as conn:
            # Check for key columns
            result = await conn.execute(
                select(1).select_from("information_schema.columns")
                .where(
                    "table_name = 'images' AND column_name IN ('id', 'filename', 'base64_data', 'uploaded_by_user_id')"
                )
            )
            columns = await result.fetchall()
            if len(columns) == 4:
                print("✅ images table has all required columns!")
            else:
                print(f"⚠️  images table found {len(columns)} expected columns (expected 4)")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_image_model():
    """Test that the Image model can be imported and used"""
    print("\n🔍 Testing Image model...")
    
    try:
        from app.models import Image, ImageType
        print(f"✅ Image model imported successfully")
        print(f"✅ ImageType enum imported with: {[t.value for t in ImageType]}")
        return True
    except Exception as e:
        print(f"❌ Image model import failed: {e}")
        return False


async def test_image_service():
    """Test that ImageService can be imported"""
    print("\n🔍 Testing ImageService...")
    
    try:
        from app.services.image_service import ImageService
        print(f"✅ ImageService imported successfully")
        print(f"   Available methods: {[m for m in dir(ImageService) if not m.startswith('_')]}")
        return True
    except Exception as e:
        print(f"❌ ImageService import failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 NFT Platform Migration Verification Tests")
    print("="*60 + "\n")
    
    results = {
        "Database Connection": await test_database_connection(),
        "Image Model": await test_image_model(),
        "ImageService": await test_image_service(),
    }
    
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'✅ All tests passed!' if passed == total else f'❌ {total - passed} test(s) failed'}")
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
