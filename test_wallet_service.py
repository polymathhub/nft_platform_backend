#!/usr/bin/env python3
"""
Quick test script to verify wallet creation endpoint works.
Run this after the backend is started.
"""

import asyncio
import httpx
import uuid
from typing import Optional

BASE_URL = "http://localhost:8000"


async def test_wallet_creation():
    """Test wallet creation endpoint."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Generate a test user ID
        test_user_id = str(uuid.uuid4())
        
        print(f"\n🧪 Testing Wallet Creation Endpoint")
        print(f"   User ID: {test_user_id}")
        print(f"   Endpoint: POST /api/v1/wallets/create?user_id={test_user_id}")
        
        # Test wallet creation for different blockchains
        blockchains = ["ethereum", "solana", "ton", "bitcoin", "polygon"]
        
        for blockchain in blockchains:
            print(f"\n   📦 Creating {blockchain.upper()} wallet...")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/wallets/create?user_id={test_user_id}",
                    json={
                        "blockchain": blockchain,
                        "wallet_type": "custodial",
                        "is_primary": blockchain == "ethereum",  # Make ETH primary
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        wallet = data.get("wallet", {})
                        print(f"      ✅ SUCCESS")
                        print(f"         Wallet ID: {wallet.get('id')}")
                        print(f"         Address: {wallet.get('address')}")
                        print(f"         Type: {wallet.get('wallet_type')}")
                    else:
                        print(f"      ❌ FAILED: {data}")
                elif response.status_code == 404:
                    print(f"      ⚠️  User not found (404). Need to create user first.")
                else:
                    print(f"      ❌ ERROR {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"      ❌ Exception: {e}")


async def test_wallet_list():
    """Test wallet listing endpoint."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        test_user_id = str(uuid.uuid4())
        
        print(f"\n🧪 Testing Wallet List Endpoint")
        print(f"   User ID: {test_user_id}")
        print(f"   Endpoint: GET /api/v1/wallets?user_id={test_user_id}")
        
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/wallets?user_id={test_user_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Response received")
                print(f"      Wallets: {len(data) if isinstance(data, list) else 'N/A'}")
            else:
                print(f"   ❌ ERROR {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")


async def test_health():
    """Test health endpoint."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        print(f"\n🧪 Testing Health Endpoint")
        print(f"   Endpoint: GET /health")
        
        try:
            response = await client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Backend is healthy")
                print(f"      Status: {data.get('status')}")
                print(f"      Telegram Bot: {'✅' if data.get('telegram_bot_token') else '❌'}")
                print(f"      Database: {'✅' if 'configured' in str(data.get('database_url')) else '❌'}")
            else:
                print(f"   ❌ Backend returned {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Backend not running: {e}")


async def main():
    """Run all tests."""
    print("=" * 70)
    print("NFT Platform Backend - Wallet Service Test")
    print("=" * 70)
    
    # Check if backend is running
    try:
        await test_health()
    except Exception as e:
        print(f"\n❌ Cannot reach backend at {BASE_URL}")
        print(f"   Make sure the backend is running: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return
    
    # Test wallet endpoints
    await test_wallet_creation()
    await test_wallet_list()
    
    print("\n" + "=" * 70)
    print("Tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
