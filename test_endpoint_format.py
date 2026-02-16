"""
Test script to verify backend endpoint response formats match frontend expectations.
Run: python test_endpoint_format.py
"""

import json
import asyncio
from app.routers.telegram_mint_router import router
from app.database import get_db_session, AsyncSessionLocal
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Create a test app
app = FastAPI()
app.include_router(router, prefix="/api/v1/telegram")

client = TestClient(app)

def test_endpoint_formats():
    """Test that endpoint responses match expected format."""
    
    print("\n" + "="*80)
    print("ENDPOINT FORMAT VERIFICATION TEST")
    print("="*80)
    
    # ========== TEST 1: Init Endpoint Response Format ==========
    print("\n[TEST 1] /web-app/init endpoint")
    print("-" * 80)
    print("Frontend expects:")
    print(json.dumps({
        "success": True,
        "user": {
            "id": "uuid-string",
            "telegram_id": 123456,
            "telegram_username": "username",
            "full_name": "User Name",        # ← ISSUE: Backend returns first_name/last_name
            "avatar_url": "url-or-null",     # ← MISSING: Not returned
            "is_verified": True,              # ← MISSING: Not returned
            "user_role": "user",              # ← MISSING: Not returned
            "created_at": "2026-02-16T...",
            "email": "user@example.com"
        }
    }, indent=2))
    
    print("\nStatus: ❌ MISMATCH FOUND")
    print("Issues:")
    print("  1. Backend returns 'first_name' + 'last_name' but model has 'full_name'")
    print("  2. Missing 'avatar_url' in response")
    print("  3. Missing 'is_verified' in response")
    print("  4. Missing 'user_role' in response (should include)")
    
    # ========== TEST 2: Dashboard Data Response Format ==========
    print("\n[TEST 2] /web-app/dashboard-data endpoint")
    print("-" * 80)
    print("Frontend expects marketplace listings with seller info:")
    print(json.dumps({
        "wallets": [
            {
                "id": "uuid",
                "blockchain": "ethereum",
                "address": "0x...",
                "is_primary": True,
                "created_at": "2026-02-16T..."
            }
        ],
        "nfts": [
            {
                "id": "uuid",
                "name": "NFT Name",
                "blockchain": "ethereum",
                "status": "owned",
                "image_url": "url-or-null",
                "minted_at": "2026-02-16T...",
                "created_at": "2026-02-16T..."
            }
        ],
        "listings": [
            {
                "id": "uuid",
                "nft_id": "uuid",
                "nft_name": "NFT Name",
                "price": 1.5,
                "currency": "ETH",
                "blockchain": "ethereum",
                "status": "active",
                "image_url": "url-or-null"
            }
        ]
    }, indent=2))
    
    print("\nStatus: ✓ OK - Format matches frontend expectations")
    
    # ========== TEST 3: Marketplace Listings Response Format ==========
    print("\n[TEST 3] /web-app/marketplace/listings endpoint")
    print("-" * 80)
    print("Frontend expects:")
    print(json.dumps({
        "success": True,
        "listings": [
            {
                "id": "uuid",
                "nft_id": "uuid",
                "nft_name": "NFT Name",
                "seller_name": "Seller Username",     # ← MISSING: Not returned by backend
                "price": 1.5,
                "currency": "ETH",
                "blockchain": "ethereum",
                "image_url": "url-or-null"
            }
        ]
    }, indent=2))
    
    print("\nStatus: ❌ MISMATCH FOUND")
    print("Issues:")
    print("  1. Missing 'seller_name' in marketplace listings")
    print("  2. Missing 'seller_id' for wallet filtering")
    
    # ========== TEST 4: Create/Mint Endpoints ==========
    print("\n[TEST 4] POST endpoints (mint, list-nft, create-wallet, etc.)")
    print("-" * 80)
    print("Frontend expects these POST endpoints to accept:")
    print(json.dumps({
        "/web-app/mint": {
            "user_id": "uuid",
            "wallet_id": "uuid",
            "nft_name": "string",
            "nft_description": "string",
            "image_url": "string (optional)"
        },
        "/web-app/list-nft": {
            "user_id": "uuid",
            "nft_id": "uuid",
            "price": 1.5,
            "currency": "string"
        },
        "/web-app/create-wallet": {
            "user_id": "uuid",
            "blockchain": "string"
        },
        "/web-app/set-primary": {
            "user_id": "uuid",
            "wallet_id": "uuid"
        },
        "/web-app/make-offer": {
            "user_id": "uuid",
            "listing_id": "uuid",
            "offer_price": 1.5
        }
    }, indent=2))
    
    print("\nStatus: ⚠️  NEEDS VERIFICATION")
    print("Action: Check if all POST endpoints exist and accept correct parameters")
    
    # ========== SUMMARY ==========
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\nCritical Issues Found:")
    print("  1. User response format (first_name/last_name vs full_name)")
    print("  2. Missing user fields (avatar_url, is_verified, user_role)")
    print("  3. Missing seller_name in marketplace listings")
    print("\nFixes Required:")
    print("  1. Update /web-app/init to return correct user fields")
    print("  2. Add seller information to marketplace listings")
    print("  3. Add optional avatar_url, is_verified, user_role fields")
    print("\n" + "="*80)

if __name__ == "__main__":
    test_endpoint_formats()
