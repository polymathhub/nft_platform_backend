"""Telegram dashboard service for user stats and quick actions."""

import logging
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta

from app.models import User, Wallet, NFT
from app.models.marketplace import Listing, ListingStatus

logger = logging.getLogger(__name__)


class TelegramDashboardService:
    """Service for dashboard stats and analytics."""

    @staticmethod
    async def get_user_dashboard_stats(db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        """Get user dashboard statistics."""
        try:
            logger.warning(f"[DASHBOARD_SERVICE] Starting to get stats for user {user_id}")
            
            # Get wallet count
            logger.warning(f"[DASHBOARD_SERVICE] Querying wallets...")
            wallets = await db.execute(
                select(Wallet).where(Wallet.user_id == user_id)
            )
            wallet_count = len(wallets.scalars().all())
            logger.warning(f"[DASHBOARD_SERVICE] Found {wallet_count} wallets")

            # Get NFT count
            logger.warning(f"[DASHBOARD_SERVICE] Querying NFTs...")
            nfts = await db.execute(
                select(NFT).where(NFT.user_id == user_id)
            )
            nft_count = len(nfts.scalars().all())
            logger.warning(f"[DASHBOARD_SERVICE] Found {nft_count} NFTs")
            
            # Get minted NFTs
            logger.warning(f"[DASHBOARD_SERVICE] Querying minted NFTs...")
            minted = await db.execute(
                select(NFT).where(
                    and_(NFT.user_id == user_id, NFT.status == "minted")
                )
            )
            minted_count = len(minted.scalars().all())
            logger.warning(f"[DASHBOARD_SERVICE] Found {minted_count} minted NFTs")

            # Get active listings
            logger.warning(f"[DASHBOARD_SERVICE] Querying listings...")
            listings = await db.execute(
                select(Listing).where(
                    and_(Listing.seller_id == user_id, Listing.status == ListingStatus.ACTIVE)
                )
            )
            listings_count = len(listings.scalars().all())
            logger.warning(f"[DASHBOARD_SERVICE] Found {listings_count} active listings")

            result = {
                "wallets": wallet_count,
                "nfts": nft_count,
                "minted": minted_count,
                "active_listings": listings_count,
                "total_value_usd": 0,
            }
            logger.warning(f"[DASHBOARD_SERVICE] Returning stats: {result}")
            return result
            
        except Exception as e:
            logger.error(f"[DASHBOARD_SERVICE] Error getting dashboard stats: {type(e).__name__}: {e}", exc_info=True)
            return {
                "wallets": 0,
                "nfts": 0,
                "minted": 0,
                "active_listings": 0,
                "total_value_usd": 0,
            }

    @staticmethod
    def format_dashboard_message(username: str, stats: Dict[str, Any]) -> str:
        """Format dashboard message with stats."""
        return (
            f"<b>Your Dashboard</b>\n\n"
            f"<b>Welcome back, {username}!</b>\n\n"
            f"<b>Your Stats:</b>\n"
            f"<b>Wallets:</b> <code>{stats['wallets']}</code>\n"
            f"<b>NFTs:</b> <code>{stats['nfts']}</code>\n"
            f"<b>Minted:</b> <code>{stats['minted']}</code>\n"
            f"<b>Listings:</b> <code>{stats['active_listings']}</code>\n\n"
            f"<b>Quick Actions:</b>\n"
            f"Use the buttons below to mint, trade, or manage your wallets."
        )

    @staticmethod
    async def build_quick_mint_message(db: AsyncSession, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get quick mint suggestion with wallet."""
        try:
            # Get primary wallet
            result = await db.execute(
                select(Wallet).where(
                    and_(Wallet.user_id == user_id, Wallet.is_primary == True)
                )
            )
            wallet = result.scalar_one_or_none()

            if not wallet:
                return None

            return {
                "wallet_id": str(wallet.id),
                "wallet_name": wallet.name or f"{wallet.blockchain.value.upper()} Wallet",
                "blockchain": wallet.blockchain.value,
                "address": wallet.address[:10] + "..." + wallet.address[-10:],
            }
        except Exception as e:
            logger.error(f"Error building quick mint: {e}")
            return None

    @staticmethod
    def format_quick_mint_message(wallet: Dict[str, Any]) -> str:
        """Format quick mint message."""
        return (
            f"<b>Quick Mint</b>\n\n"
            f"Your primary wallet is ready:\n\n"
            f"<b>{wallet['wallet_name']}</b>\n"
            f"Chain: <code>{wallet['blockchain'].upper()}</code>\n"
            f"Address: <code>{wallet['address']}</code>\n\n"
            f"<b>Tap the button below to mint your first NFT!</b>"
        )
