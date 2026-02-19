#!/usr/bin/env python3
"""
Test script to verify wallet creation and import endpoints work with updated schemas.
Tests blockchain value normalization and validation.
"""
import asyncio
import aiohttp
import json
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000/api/v1/telegram/web-app"

# Test data - simulate Telegram init_data
TEST_INIT_DATA = {
    "query_id": "test_query_123",
    "user": {
        "id": 123456789,
        "is_bot": False,
        "first_name": "Test",
        "username": "testuser",
        "language_code": "en"
    },
    "auth_date": int(datetime.now(timezone.utc).timestamp()),
    "hash": "test_hash"
}

async def test_wallet_creation():
    """Test wallet creation with different blockchain formats"""
    async with aiohttp.ClientSession() as session:
        print("\n" + "="*60)
        print("WALLET CREATION TESTS")
        print("="*60)
        
        test_cases = [
            {
                "name": "Create Ethereum wallet (lowercase)",
                "blockchain": "ethereum",
                "wallet_type": "custodial",
                "description": "Testing lowercase blockchain value"
            },
            {
                "name": "Create Bitcoin wallet (lowercase)",
                "blockchain": "bitcoin",
                "wallet_type": "custodial",
                "description": "Testing Bitcoin blockchain"
            },
            {
                "name": "Create Solana wallet (lowercase)",
                "blockchain": "solana",
                "wallet_type": "custodial",
                "description": "Testing Solana blockchain"
            },
            {
                "name": "Create TON wallet (lowercase)",
                "blockchain": "ton",
                "wallet_type": "custodial",
                "description": "Testing TON blockchain"
            },
            {
                "name": "Invalid blockchain",
                "blockchain": "invalid_chain",
                "wallet_type": "custodial",
                "expected_error": True,
                "description": "Testing invalid blockchain rejection"
            },
        ]
        
        for test_case in test_cases:
            print(f"\n▶ {test_case['name']}")
            print(f"  Description: {test_case['description']}")
            
            request_body = {
                "blockchain": test_case["blockchain"],
                "wallet_type": test_case["wallet_type"],
                "is_primary": True,
                "init_data": json.dumps(TEST_INIT_DATA)
            }
            
            print(f"  Request: {json.dumps(request_body, indent=4)}")
            
            try:
                async with session.post(
                    f"{BASE_URL}/create-wallet",
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data = await resp.json()
                    
                    if test_case.get("expected_error"):
                        if resp.status >= 400:
                            print(f"  ✓ Correctly rejected (Status {resp.status})")
                            print(f"    Error: {data.get('detail', 'Unknown error')}")
                        else:
                            print(f"  ✗ Expected error but got success (Status {resp.status})")
                            print(f"    Response: {json.dumps(data, indent=4)}")
                    else:
                        if resp.status == 200:
                            print(f"  ✓ Success (Status {resp.status})")
                            if data.get("success"):
                                wallet = data.get("wallet", {})
                                print(f"    Wallet ID: {wallet.get('id')}")
                                print(f"    Blockchain: {wallet.get('blockchain')}")
                                print(f"    Is Primary: {wallet.get('is_primary')}")
                            else:
                                print(f"    Response: {json.dumps(data, indent=4)}")
                        else:
                            print(f"  ✗ Failed (Status {resp.status})")
                            print(f"    Error: {data.get('detail', 'Unknown error')}")
                            
            except asyncio.TimeoutError:
                print(f"  ✗ Request timeout")
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")


async def test_wallet_import():
    """Test wallet import with different blockchain formats"""
    async with aiohttp.ClientSession() as session:
        print("\n" + "="*60)
        print("WALLET IMPORT TESTS")
        print("="*60)
        
        test_cases = [
            {
                "name": "Import Ethereum wallet",
                "blockchain": "ethereum",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f42bE7",
                "description": "Testing Ethereum import with valid address"
            },
            {
                "name": "Import Bitcoin wallet",
                "blockchain": "bitcoin",
                "address": "1A1z7agoat2LWQLW2cYc6Kia6vqwuV2hL3",
                "description": "Testing Bitcoin import with valid address"
            },
            {
                "name": "Import Solana wallet",
                "blockchain": "solana",
                "address": "TokenkegQfeZyiNwAJsNFAD1j3jjZkyodm3qLJbQ53QwZ",
                "description": "Testing Solana import with valid address"
            },
            {
                "name": "Invalid blockchain in import",
                "blockchain": "invalid_network",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f42bE7",
                "expected_error": True,
                "description": "Testing invalid blockchain rejection in import"
            },
        ]
        
        for test_case in test_cases:
            print(f"\n▶ {test_case['name']}")
            print(f"  Description: {test_case['description']}")
            
            request_body = {
                "blockchain": test_case["blockchain"],
                "address": test_case["address"],
                "is_primary": True,
                "init_data": json.dumps(TEST_INIT_DATA)
            }
            
            print(f"  Request: {json.dumps(request_body, indent=4)}")
            
            try:
                async with session.post(
                    f"{BASE_URL}/import-wallet",
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data = await resp.json()
                    
                    if test_case.get("expected_error"):
                        if resp.status >= 400:
                            print(f"  ✓ Correctly rejected (Status {resp.status})")
                            print(f"    Error: {data.get('detail', 'Unknown error')}")
                        else:
                            print(f"  ✗ Expected error but got success (Status {resp.status})")
                            print(f"    Response: {json.dumps(data, indent=4)}")
                    else:
                        if resp.status == 200:
                            print(f"  ✓ Success (Status {resp.status})")
                            if data.get("success"):
                                wallet = data.get("wallet", {})
                                print(f"    Wallet ID: {wallet.get('id')}")
                                print(f"    Blockchain: {wallet.get('blockchain')}")
                                print(f"    Address: {wallet.get('address')}")
                                print(f"    Is Primary: {wallet.get('is_primary')}")
                            else:
                                print(f"    Response: {json.dumps(data, indent=4)}")
                        else:
                            print(f"  ✗ Failed (Status {resp.status})")
                            print(f"    Error: {data.get('detail', 'Unknown error')}")
                            
            except asyncio.TimeoutError:
                print(f"  ✗ Request timeout")
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")


async def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║  Wallet Creation & Import Test Suite - Schema Validation   ║
║  Tests blockchain value normalization and validation       ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    print("\nNote: This test requires the backend server running at http://localhost:8000")
    print("Command: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    
    try:
        # Test both endpoints
        await test_wallet_creation()
        await test_wallet_import()
        
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        print("\n✓ If you see success messages above, the fixes are working!")
        print("✗ If you see errors, check:")
        print("  1. Backend server is running at http://localhost:8000")
        print("  2. Database is initialized and accessible")
        print("  3. Telegram WebApp initialization data is valid")
        
    except Exception as e:
        print(f"\n✗ Test suite error: {str(e)}")
        print("Make sure the backend server is running before running this test.")


if __name__ == "__main__":
    asyncio.run(main())
