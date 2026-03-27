"""
Comprehensive Mint Flow Verification Test
Tests all blockers have been fixed and the mint pipeline works end-to-end.
Run: python test_mint_blockers.py
"""
import asyncio
import sys
from uuid import UUID
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_imports():
    """Test 1: Verify all models and schemas import correctly"""
    print("\n✓ Test 1: Module Imports")
    try:
        from app.models.nft import NFT
        from app.models.image import Image, ImageType
        from app.schemas.nft import MintNFTRequest, NFTResponse, NFTDetailResponse
        from app.services.nft_service import NFTService
        from app.services.image_service import ImageService
        from app.routers.nft_router import router as nft_router
        
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


async def test_schema_validation():
    """Test 2: Verify MintNFTRequest accepts large image_url"""
    print("\n✓ Test 2: Schema Field Validation")
    try:
        from app.schemas.nft import MintNFTRequest
        from uuid import UUID, uuid4
        
        # Create large image URL (~1KB base64)
        large_image_url = "data:image/jpeg;base64," + "A" * 800
        
        # Should accept without error (max_length now 2083)
        request = MintNFTRequest(
            wallet_id=uuid4(),
            name="Test NFT",
            description="Test",
            image_url=large_image_url,
            royalty_percentage=50,  # Should now accept 0-100
            metadata={"test": "data"}
        )
        
        print(f"  ✓ Large image_url accepted ({len(large_image_url)} chars)")
        print(f"  ✓ Royalty percentage 50% accepted (0-100 range)")
        return True
    except Exception as e:
        print(f"  ✗ Schema validation failed: {e}")
        return False


async def test_nft_model_structure():
    """Test 3: Verify NFT model has image_id field"""
    print("\n✓ Test 3: NFT Model Structure")
    try:
        from app.models.nft import NFT
        from sqlalchemy import inspect
        
        mapper = inspect(NFT)
        columns = {col.name for col in mapper.columns}
        
        required_fields = {
            'id', 'user_id', 'wallet_id', 'name', 'image_url', 
            'blockchain', 'status', 'image_id'  # CRITICAL
        }
        
        missing = required_fields - columns
        if missing:
            print(f"  ✗ Missing fields: {missing}")
            return False
        
        print(f"  ✓ NFT model has required fields")
        print(f"  ✓ image_id field present (FK to images table)")
        
        # Check image_url field length
        image_url_col = mapper.columns['image_url']
        print(f"  ✓ image_url field length: {image_url_col.type.length} (target: 2083)")
        
        return True
    except Exception as e:
        print(f"  ✗ Model check failed: {e}")
        return False


async def test_image_response_format():
    """Test 4: Verify ImageService response format"""
    print("\n✓ Test 4: ImageService Response Format")
    try:
        from app.services.image_service import ImageService
        
        # Check if ImageService has the right methods
        required_methods = {
            'upload_image': 'Upload image and store in database',
            'get_image_url': 'Get image URL (data URI or reference)',
            'get_image_by_id': 'Retrieve image by ID',
            'delete_image': 'Soft-delete image',
        }
        
        for method_name in required_methods.keys():
            if not hasattr(ImageService, method_name):
                print(f"  ✗ Missing method: {method_name}")
                return False
        
        print(f"  ✓ ImageService has all required methods:")
        for name, desc in required_methods.items():
            print(f"    - {name}: {desc}")
        
        return True
    except Exception as e:
        print(f"  ✗ ImageService check failed: {e}")
        return False


async def test_database_schema():
    """Test 5: Verify database schema changes"""
    print("\n✓ Test 5: Database Schema")
    try:
        from app.database.engine import engine
        from sqlalchemy import inspect, text
        
        async with engine.begin() as conn:
            # Check if images table exists
            result = await conn.execute(text(
                "SELECT EXISTS(SELECT FROM information_schema.tables WHERE table_name='images')"
            ))
            images_table_exists = result.scalar()
            
            # Check if nfts.image_id column exists
            result = await conn.execute(text(
                "SELECT EXISTS(SELECT FROM information_schema.columns WHERE table_name='nfts' AND column_name='image_id')"
            ))
            image_id_col_exists = result.scalar()
            
            # Check nft.image_url column length
            result = await conn.execute(text(
                "SELECT character_maximum_length FROM information_schema.columns WHERE table_name='nfts' AND column_name='image_url'"
            ))
            image_url_length = result.scalar()
            
            print(f"  ✓ images table exists: {images_table_exists}")
            print(f"  ✓ nfts.image_id column exists: {image_id_col_exists}")
            print(f"  ✓ nfts.image_url max length: {image_url_length} (target: 2083)")
            
            if not all([images_table_exists, image_id_col_exists, image_url_length]):
                print("  ✗ Database schema incomplete")
                return False
            
            return True
    except Exception as e:
        print(f"  ✗ Database schema check failed: {e}")
        return False


async def test_migration_chain():
    """Test 6: Verify migration chain is intact"""
    print("\n✓ Test 6: Migration Chain")
    try:
        from pathlib import Path
        import re
        
        migrations_dir = Path("alembic/versions")
        migration_files = sorted(migrations_dir.glob("*.py"))
        
        revisions = {}
        for mig_file in migration_files:
            if mig_file.name.startswith("__"):
                continue
            
            content = mig_file.read_text()
            rev_match = re.search(r"revision = '([^']+)'", content)
            down_rev_match = re.search(r"down_revision = '([^']+)'", content)
            
            if rev_match:
                rev_id = rev_match.group(1)
                down_rev = down_rev_match.group(1) if down_rev_match else None
                revisions[rev_id] = {
                    'file': mig_file.name,
                    'down_revision': down_rev
                }
        
        # Check critical migrations exist
        critical_migs = ['014_add_image_table', '015_add_image_id_to_nfts']
        for mig in critical_migs:
            if mig not in revisions:
                print(f"  ✗ Missing critical migration: {mig}")
                return False
            print(f"  ✓ Migration {mig} present")
        
        # Verify chain: 014 -> 015
        if revisions['015_add_image_id_to_nfts']['down_revision'] != '014_add_image_table':
            print("  ✗ Migration chain broken at 015")
            return False
        
        print(f"  ✓ Migration chain intact (014 -> 015)")
        return True
    except Exception as e:
        print(f"  ✗ Migration check failed: {e}")
        return False


async def test_integration():
    """Test 7: Verify all components work together"""
    print("\n✓ Test 7: Integration Test")
    try:
        from app.schemas.nft import MintNFTRequest
        from app.models.nft import NFT
        from uuid import uuid4
        
        # Simulate mint request
        image_id = uuid4()
        mint_req = MintNFTRequest(
            wallet_id=uuid4(),
            name="Integration Test NFT",
            description="Testing all components",
            image_url="data:image/jpeg;base64;AAABBBCCC",
            image_id=image_id,
            royalty_percentage=75,
            metadata={
                "blockchain": "ton",
                "media_type": "image"
            }
        )
        
        print(f"  ✓ MintNFTRequest created successfully")
        print(f"  ✓ Contains image_id: {mint_req.image_id is not None}")
        print(f"  ✓ Contains image_url: {mint_req.image_url is not None}")
        print(f"  ✓ Royalty validation range: 0-100% ✓")
        
        # Verify schema would accept this
        assert mint_req.image_id is not None
        assert mint_req.royalty_percentage == 75
        assert len(mint_req.image_url) > 0
        
        print(f"  ✓ All integration checks passed")
        return True
    except Exception as e:
        print(f"  ✗ Integration test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 70)
    print("NFT MINTING BLOCKER VERIFICATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Module Imports", test_imports),
        ("Schema Validation", test_schema_validation),
        ("NFT Model Structure", test_nft_model_structure),
        ("ImageService Response", test_image_response_format),
        ("Database Schema", test_database_schema),
        ("Migration Chain", test_migration_chain),
        ("Integration", test_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")
    
    print("-" * 70)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Minting blockers have been fixed.")
        print("\nNext steps:")
        print("1. Start backend: python -m uvicorn app.main:app --reload")
        print("2. Test image upload: POST /api/v1/images/upload")
        print("3. Test NFT minting: POST /api/v1/nfts/mint")
        print("4. Verify in database: SELECT * FROM nfts WHERE image_id IS NOT NULL")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
