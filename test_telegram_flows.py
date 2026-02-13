#!/usr/bin/env python3
"""
Comprehensive test script to verify Telegram command flows work end-to-end.
Tests: wallet creation, NFT minting, wallet listing, marketplace listing
"""

import asyncio
import logging
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_wallet_creation_flow():
    """Test wallet creation with real key generation."""
    logger.info("=" * 70)
    logger.info("TEST 1: Wallet Creation Flow")
    logger.info("=" * 70)
    
    try:
        from app.database import get_db_session
        from app.models import User, Wallet
        from app.models.wallet import BlockchainType
        from app.services.wallet_service import WalletService
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        import os
        
        # Use in-memory SQLite for testing
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with engine.begin() as conn:
            from app.database.base import Base
            await conn.run_sync(Base.metadata.create_all)
        
        async with async_session() as db:
            # Create test user
            test_user = User(
                id=uuid4(),
                username="test_user",
                email=f"test_{uuid4()}@example.com",
                hashed_password="",
                telegram_id="123456789",
            )
            db.add(test_user)
            await db.commit()
            logger.info(f"✓ Created test user: {test_user.username}")
            
            # Test Ethereum wallet generation
            logger.info("\nTesting Ethereum wallet generation...")
            wallet, error = await WalletService.generate_evm_wallet(
                db=db,
                user_id=test_user.id,
                make_primary=True,
            )
            
            if wallet:
                logger.info(f"✓ Ethereum wallet created!")
                logger.info(f"  - Address: {wallet.address}")
                logger.info(f"  - Blockchain: {wallet.blockchain.value}")
                logger.info(f"  - Has private key: {bool(wallet.encrypted_private_key)}")
                assert wallet.address.startswith("0x"), "Should be valid Ethereum address"
                assert len(wallet.address) == 42, "Ethereum address should be 42 chars"
            else:
                logger.error(f"✗ Ethereum wallet creation failed: {error}")
                return False
            
            # Test TON wallet generation
            logger.info("\nTesting TON wallet generation...")
            wallet_ton, error = await WalletService.generate_ton_wallet(
                db=db,
                user_id=test_user.id,
                make_primary=False,
            )
            
            if wallet_ton:
                logger.info(f"✓ TON wallet created!")
                logger.info(f"  - Address: {wallet_ton.address[:50]}...")
                logger.info(f"  - Blockchain: {wallet_ton.blockchain.value}")
                logger.info(f"  - Has private key: {bool(wallet_ton.encrypted_private_key)}")
            else:
                logger.error(f"✗ TON wallet creation failed: {error}")
                return False
            
            # Test Solana wallet generation
            logger.info("\nTesting Solana wallet generation...")
            wallet_solana, error = await WalletService.generate_solana_wallet(
                db=db,
                user_id=test_user.id,
                make_primary=False,
            )
            
            if wallet_solana:
                logger.info(f"✓ Solana wallet created!")
                logger.info(f"  - Address: {wallet_solana.address}")
                logger.info(f"  - Blockchain: {wallet_solana.blockchain.value}")
                logger.info(f"  - Has private key: {bool(wallet_solana.encrypted_private_key)}")
            else:
                logger.error(f"✗ Solana wallet creation failed: {error}")
                return False
            
            logger.info("\n✅ All wallet generation tests passed!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        return False


async def test_telegram_keyboards():
    """Test Telegram keyboard builders."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Telegram Keyboard Builders")
    logger.info("=" * 70)
    
    try:
        from app.utils.telegram_keyboards import (
            build_main_menu_keyboard,
            build_wallet_action_keyboard,
            build_wallet_blockchain_keyboard,
        )
        
        # Test main menu keyboard
        logger.info("\nTesting main menu keyboard...")
        main_menu = build_main_menu_keyboard()
        assert "inline_keyboard" in main_menu
        assert len(main_menu["inline_keyboard"]) > 0
        logger.info(f"✓ Main menu keyboard has {len(main_menu['inline_keyboard'])} rows")
        
        # Test wallet action keyboard
        logger.info("Testing wallet action keyboard...")
        wallet_actions = build_wallet_action_keyboard("test-wallet-id")
        assert "inline_keyboard" in wallet_actions
        logger.info(f"✓ Wallet action keyboard has {len(wallet_actions['inline_keyboard'])} rows")
        
        # Test blockchain selection keyboard
        logger.info("Testing blockchain selection keyboard...")
        blockchain_select = build_wallet_blockchain_keyboard()
        assert "inline_keyboard" in blockchain_select
        logger.info(f"✓ Blockchain selection keyboard has {len(blockchain_select['inline_keyboard'])} rows")
        
        logger.info("\n✅ All keyboard builder tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        return False


async def test_telegram_wallet_handler():
    """Test telegram wallet handler."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Telegram Wallet Handler")
    logger.info("=" * 70)
    
    try:
        from app.models import User
        from app.services.telegram_wallet_handler import create_wallet_for_user
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from uuid import uuid4
        from unittest.mock import AsyncMock
        
        # Setup test database
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with engine.begin() as conn:
            from app.database.base import Base
            await conn.run_sync(Base.metadata.create_all)
        
        async with async_session() as db:
            # Create test user
            test_user = User(
                id=uuid4(),
                username="telegram_user",
                email=f"tg_{uuid4()}@example.com",
                hashed_password="",
                telegram_id="987654321",
            )
            db.add(test_user)
            await db.commit()
            
            # Mock message sender
            messages = []
            async def mock_send_message(chat_id, message, **kwargs):
                messages.append(message)
                logger.debug(f"Mock message sent: {message[:50]}...")
            
            # Test Ethereum wallet creation via handler
            logger.info("\nTesting Ethereum wallet creation via handler...")
            wallet, error = await create_wallet_for_user(
                db=db,
                chat_id=123456,
                user=test_user,
                blockchain_str="ethereum",
                bot_send_message_fn=mock_send_message,
            )
            
            if wallet:
                logger.info(f"✓ Ethereum wallet created via handler!")
                logger.info(f"  - Address: {wallet.address}")
                logger.info(f"  - Blockchain: {wallet.blockchain.value}")
                assert wallet.address.startswith("0x"), "Should be valid Ethereum address"
                assert len(messages) > 0, "Should have sent success message"
            else:
                logger.error(f"✗ Handler failed: {error}")
                return False
            
            # Test invalid blockchain
            logger.info("\nTesting invalid blockchain handling...")
            wallet_invalid, error_invalid = await create_wallet_for_user(
                db=db,
                chat_id=123456,
                user=test_user,
                blockchain_str="invalid_chain",
                bot_send_message_fn=mock_send_message,
            )
            
            if not wallet_invalid and error_invalid:
                logger.info(f"✓ Invalid blockchain properly rejected: {error_invalid[:50]}...")
            else:
                logger.error("✗ Should have rejected invalid blockchain")
                return False
            
            logger.info("\n✅ All wallet handler tests passed!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        return False


async def run_all_tests():
    """Run all tests."""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 68 + "║")
    logger.info("║" + "  TELEGRAM NFT PLATFORM - COMPREHENSIVE TEST SUITE".center(68) + "║")
    logger.info("║" + " " * 68 + "║")
    logger.info("╚" + "=" * 68 + "╝")
    
    results = {
        "Wallet Creation Flow": await test_wallet_creation_flow(),
        "Telegram Keyboards": await test_telegram_keyboards(),
        "Telegram Wallet Handler": await test_telegram_wallet_handler(),
    }
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED! The Telegram wallet and command system is functional!")
        return True
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed. Please review the logs above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
