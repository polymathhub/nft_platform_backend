#!/usr/bin/env python3
"""
Diagnostic: Check web app user data fetching from database
Verifies that each user only gets their own data
"""

import asyncio
from uuid import uuid4, UUID
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from app.database.connection import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models import User, Wallet, NFT
from app.models.marketplace import Listing, ListingStatus
from sqlalchemy import select, func

async def diagnose():
    print("\n🔍 Web App User Data Fetching Diagnosis")
    print("=" * 60)
    
    # Get a database session
    from app.database.connection import async_engine
    
    async with sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )() as db:
        # Count total users
        user_count_result = await db.execute(select(func.count(User.id)))
        total_users = user_count_result.scalar()
        print(f"\n📊 Total users in database: {total_users}")
        
        # Check if users have wallets
        users_result = await db.execute(select(User).limit(5))
        users = users_result.scalars().all()
        
        if not users:
            print("❌ No users found in database!")
            return
        
        print(f"\n✅ Found {len(users)} sample users to check\n")
        
        for user in users:
            print(f"{'─' * 60}")
            print(f"User: {user.telegram_username} (ID: {str(user.id)[:8]}...)")
            print(f"  Telegram ID: {user.telegram_id}")
            print(f"  Created: {user.created_at}")
            
            # Check wallets for this user
            wallets_result = await db.execute(
                select(Wallet).where(Wallet.user_id == user.id)
            )
            wallets = wallets_result.scalars().all()
            print(f"  💼 Wallets: {len(wallets)}")
            for w in wallets[:3]:
                print(f"      - {w.blockchain}: {w.address[:10]}...")
            
            # Check NFTs for this user
            nfts_result = await db.execute(
                select(NFT).where(NFT.user_id == user.id).limit(5)
            )
            nfts = nfts_result.scalars().all()
            print(f"  🖼️  NFTs: {len(nfts)}")
            for n in nfts[:3]:
                print(f"      - {n.name}")
            
            # Check user's listings (where they are the seller)
            listings_result = await db.execute(
                select(Listing).where(Listing.seller_id == user.id)
            )
            listings = listings_result.scalars().all()
            print(f"  🏪 Own Listings: {len(listings)}")
            for l in listings[:3]:
                print(f"      - NFT ID: {str(l.nft_id)[:8]}... Price: {l.price} {l.currency}")
        
        # Test the dashboard data query for a specific user
        print(f"\n{'=' * 60}")
        print("🧪 Testing Dashboard Data Query")
        print(f"{'=' * 60}")
        
        test_user = users[0]
        print(f"\n Testing for user: {test_user.telegram_username}")
        print(f"  User UUID: {test_user.id}")
        
        # Run the exact dashboard query
        wallets_result = await db.execute(
            select(Wallet)
            .where(Wallet.user_id == test_user.id)
            .order_by(Wallet.is_primary.desc(), Wallet.created_at.desc())
        )
        wallets = wallets_result.scalars().all()
        
        nfts_result = await db.execute(
            select(NFT)
            .where(NFT.user_id == test_user.id)
            .order_by(NFT.created_at.desc())
            .limit(50)
        )
        nfts = nfts_result.scalars().all()
        
        # Check the problematic listings query
        listings_result = await db.execute(
            select(Listing)
            .where(Listing.status == ListingStatus.ACTIVE)
            .order_by(Listing.created_at.desc())
            .limit(50)
        )
        all_listings = listings_result.scalars().all()
        
        print(f"\n  Query Results:")
        print(f"    ✅ Wallets (filtered by user): {len(wallets)}")
        print(f"    ✅ NFTs (filtered by user): {len(nfts)}")
        print(f"    ⚠️  Listings (NOT filtered by user): {len(all_listings)} total active")
        print(f"       Note: Showing ALL marketplace listings, not filtered by user")
        
        # Suggest improvement
        print(f"\n{'=' * 60}")
        print("💡 FINDINGS:")
        print(f"{'=' * 60}")
        print("""
✅ Wallets are properly filtered by user_id
✅ NFTs are properly filtered by user_id
⚠️  Listings in dashboard are NOT filtered by user

ISSUE: The /web-app/dashboard-data endpoint returns:
  - User's wallets (correct filter: where user_id = X)
  - User's NFTs (correct filter: where user_id = X)
  - ALL marketplace listings (WRONG: no user filter!)
  
FIX: The "listings" field in dashboard should show user's OWN listings
     or should be removed (use separate marketplace endpoint instead)
        """)

if __name__ == "__main__":
    asyncio.run(diagnose())
