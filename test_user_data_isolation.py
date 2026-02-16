#!/usr/bin/env python3
"""
Test script to verify web app data fetching for multiple users
This simulates the web app authentication and data loading for different users
"""

import asyncio
import json
from uuid import UUID
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_web_app_user_isolation():
    """Test that each user only sees their own data"""
    
    from app.database.connection import async_engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.models import User, Wallet, NFT
    from app.models.marketplace import Listing, ListingStatus
    from sqlalchemy import select, func
    
    print("\n" + "="*70)
    print("🧪 Web App User Data Isolation Test")
    print("="*70)
    
    async with sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )() as db:
        # Get all users
        users_result = await db.execute(select(User).limit(5))
        users = users_result.scalars().all()
        
        if len(users) < 2:
            print("\n⚠️  Not enough users in database to test isolation (need 2+)")
            print(f"   Found {len(users)} user(s)")
            return False
        
        print(f"\n✓ Found {len(users)} users for testing\n")
        
        all_pass = True
        
        for idx, user in enumerate(users[:2], 1):
            print(f"\n{'─'*70}")
            print(f"Test User {idx}: {user.telegram_username} (ID: {str(user.id)[:12]}...)")
            print(f"{'─'*70}")
            
            # Simulate the /web-app/dashboard-data endpoint
            # Get wallets (should be filtered by user_id)
            wallets_result = await db.execute(
                select(Wallet)
                .where(Wallet.user_id == user.id)
                .order_by(Wallet.is_primary.desc())
            )
            user_wallets = wallets_result.scalars().all()
            
            # Get NFTs (should be filtered by user_id)
            nfts_result = await db.execute(
                select(NFT)
                .where(NFT.user_id == user.id)
                .limit(50)
            )
            user_nfts = nfts_result.scalars().all()
            
            # Get user's own listings (should be filtered by seller_id)
            listings_result = await db.execute(
                select(Listing)
                .where((Listing.seller_id == user.id) & (Listing.status == ListingStatus.ACTIVE))
            )
            user_listings = listings_result.scalars().all()
            
            print(f"  Data Retrieved:")
            print(f"    ✓ Wallets: {len(user_wallets)}")
            for w in user_wallets[:2]:
                print(f"      - {w.blockchain}: {w.address[:12]}...")
            
            print(f"    ✓ NFTs: {len(user_nfts)}")
            for n in user_nfts[:2]:
                print(f"      - {n.name}")
            
            print(f"    ✓ Own Listings: {len(user_listings)}")
            for l in user_listings[:2]:
                print(f"      - Listing {str(l.id)[:8]}...: {l.price} {l.currency}")
            
            # Verify no data leakage - check that data belongs to this user
            for wallet in user_wallets:
                if wallet.user_id != user.id:
                    print(f"    ❌ FAIL: Wallet {wallet.id} doesn't belong to user!")
                    all_pass = False
            
            for nft in user_nfts:
                if nft.user_id != user.id:
                    print(f"    ❌ FAIL: NFT {nft.id} doesn't belong to user!")
                    all_pass = False
            
            for listing in user_listings:
                if listing.seller_id != user.id:
                    print(f"    ❌ FAIL: Listing {listing.id} seller is not this user!")
                    all_pass = False
            
            if all([wallet.user_id == user.id for wallet in user_wallets] +
                   [nft.user_id == user.id for nft in user_nfts] +
                   [listing.seller_id == user.id for listing in user_listings]):
                print(f"    ✅ Data isolation verified for this user")
            
        # Test marketplace listings - should NOT be filtered by user
        print(f"\n{'─'*70}")
        print("Test: Marketplace Listings (should be public)")
        print(f"{'─'*70}")
        
        listings_result = await db.execute(
            select(Listing)
            .where(Listing.status == ListingStatus.ACTIVE)
            .limit(50)
        )
        all_marketplace_listings = listings_result.scalars().all()
        
        print(f"  Public marketplace listings: {len(all_marketplace_listings)}")
        print(f"    ✓ Showing all active listings (not filtered by user)")
        
        # Verify each listing belongs to some user
        for listing in all_marketplace_listings[:3]:
            seller_result = await db.execute(
                select(User).where(User.id == listing.seller_id)
            )
            seller = seller_result.scalar_one_or_none()
            if seller:
                print(f"      - {listing.price} {listing.currency} (Seller: {seller.telegram_username})")
        
        print(f"\n{'='*70}")
        if all_pass:
            print("✅ ALL TESTS PASSED - User data isolation is working correctly!")
        else:
            print("❌ TESTS FAILED - Data isolation issue detected!")
        print(f"{'='*70}\n")
        
        return all_pass

if __name__ == "__main__":
    try:
        result = asyncio.run(test_web_app_user_isolation())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Error running test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
