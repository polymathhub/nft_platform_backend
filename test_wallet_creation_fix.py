#!/usr/bin/env python3
"""
Quick test to verify Telegram wallet creation is working with proper key generation.
"""

import asyncio
import sys
from uuid import uuid4
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_telegram_wallet_creation():
    """Test that wallet creation generates real keys, not dummy addresses."""
    print("\n" + "=" * 70)
    print("TELEGRAM WALLET CREATION TEST")
    print("=" * 70)
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from app.database.base import Base
        from app.models import User
        from app.services.wallet_service import WalletService
        
        # Create in-memory test database
        print("\n1️⃣ Setting up test database...")
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✓ Database created")
        
        # Create test user
        print("\n2️⃣ Creating test user...")
        async with async_session() as db:
            test_user = User(
                id=uuid4(),
                username="test_telegram_user",
                email=f"test_{uuid4()}@example.com",
                hashed_password="hashed_pwd",
                telegram_id="123456789",
            )
            db.add(test_user)
            await db.commit()
            user_id = test_user.id
            print(f"✓ Test user created: {test_user.username}")
        
        # Test Ethereum wallet creation
        print("\n3️⃣ Testing Ethereum wallet generation...")
        async with async_session() as db:
            wallet, error = await WalletService.generate_evm_wallet(
                db=db,
                user_id=user_id,
                make_primary=True,
            )
            
            if not wallet:
                print(f"❌ FAILED: {error}")
                return False
            
            print(f"✓ Ethereum wallet created!")
            print(f"  - Address: {wallet.address}")
            print(f"  - Length: {len(wallet.address)} chars")
            print(f"  - Has encrypted private key: {bool(wallet.encrypted_private_key)}")
            print(f"  - Blockchain: {wallet.blockchain.value}")
            
            # Validate address format
            if not wallet.address.startswith("0x"):
                print(f"❌ FAILED: Address doesn't start with 0x")
                return False
            
            if len(wallet.address) != 42:
                print(f"❌ FAILED: Ethereum address should be 42 chars, got {len(wallet.address)}")
                return False
            
            if not wallet.encrypted_private_key:
                print(f"❌ FAILED: No encrypted private key stored")
                return False
            
            print("✓ All Ethereum wallet validations passed!")
        
        # Test Solana wallet creation
        print("\n4️⃣ Testing Solana wallet generation...")
        async with async_session() as db:
            wallet_sol, error = await WalletService.generate_solana_wallet(
                db=db,
                user_id=user_id,
                make_primary=False,
            )
            
            if not wallet_sol:
                print(f"❌ FAILED: {error}")
                return False
            
            print(f"✓ Solana wallet created!")
            print(f"  - Address: {wallet_sol.address}")
            print(f"  - Has encrypted private key: {bool(wallet_sol.encrypted_private_key)}")
            print(f"  - Blockchain: {wallet_sol.blockchain.value}")
            
            if not wallet_sol.encrypted_private_key:
                print(f"❌ FAILED: No encrypted private key for Solana")
                return False
            
            print("✓ All Solana wallet validations passed!")
        
        # Test TON wallet creation
        print("\n5️⃣ Testing TON wallet generation...")
        async with async_session() as db:
            wallet_ton, error = await WalletService.generate_ton_wallet(
                db=db,
                user_id=user_id,
                make_primary=False,
            )
            
            if not wallet_ton:
                print(f"❌ FAILED: {error}")
                return False
            
            print(f"✓ TON wallet created!")
            print(f"  - Address: {wallet_ton.address[:50]}...")
            print(f"  - Has encrypted private key: {bool(wallet_ton.encrypted_private_key)}")
            print(f"  - Blockchain: {wallet_ton.blockchain.value}")
            
            if not wallet_ton.encrypted_private_key:
                print(f"❌ FAILED: No encrypted private key for TON")
                return False
            
            print("✓ All TON wallet validations passed!")
        
        # Test Bitcoin wallet creation
        print("\n6️⃣ Testing Bitcoin wallet generation...")
        async with async_session() as db:
            wallet_btc, error = await WalletService.generate_bitcoin_wallet(
                db=db,
                user_id=user_id,
                make_primary=False,
            )
            
            if not wallet_btc:
                print(f"❌ FAILED: {error}")
                return False
            
            print(f"✓ Bitcoin wallet created!")
            print(f"  - Address: {wallet_btc.address}")
            print(f"  - Has encrypted private key: {bool(wallet_btc.encrypted_private_key)}")
            print(f"  - Blockchain: {wallet_btc.blockchain.value}")
            
            # Bitcoin addresses can be legacy (1...), P2SH (3...), or Bech32 (bc1...)
            valid_prefix = wallet_btc.address[0] in ['1', '3', 'b']
            if not valid_prefix:
                print(f"❌ FAILED: Invalid Bitcoin address prefix")
                return False
            
            if not wallet_btc.encrypted_private_key:
                print(f"❌ FAILED: No encrypted private key for Bitcoin")
                return False
            
            print("✓ All Bitcoin wallet validations passed!")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nWallet creation is now using proper key generation.")
        print("The /wallet-create command should work correctly in Telegram.")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_telegram_wallet_creation())
    sys.exit(0 if success else 1)
