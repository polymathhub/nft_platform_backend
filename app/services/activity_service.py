"""
Activity Logging Service - Centralized activity tracking.
All operations log to ActivityLog for audit trail and user history.
"""

import logging
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

from app.models.activity import ActivityLog, ActivityType

logger = logging.getLogger(__name__)


class ActivityService:
    """Service for logging user activities to audit trail."""

    @staticmethod
    async def log_activity(
        db: AsyncSession,
        user_id: UUID,
        activity_type: ActivityType,
        description: str = None,
        resource_type: str = None,
        resource_id: str = None,
        metadata: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
        status: str = "success",
        error_message: str = None,
        telegram_id: str = None,
        telegram_username: str = None,
    ) -> ActivityLog:
        """
        Log an activity for a user.
        
        Args:
            db: Database session
            user_id: UUID of the user
            activity_type: Type of activity (from ActivityType enum)
            description: Human-readable description
            resource_type: Type of resource affected (wallet, nft, listing, etc.)
            resource_id: ID of the resource affected
            metadata: Additional context as dict
            ip_address: Client IP address
            user_agent: Client user agent
            status: success/failed/pending
            error_message: Error message if failed
            telegram_id: User's Telegram ID (for logging)
            telegram_username: User's Telegram username (for identification)
        
        Returns:
            Created ActivityLog object
        """
        try:
            activity = ActivityLog(
                user_id=user_id,
                telegram_id=telegram_id,
                telegram_username=telegram_username,
                activity_type=activity_type,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                activity_metadata=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                error_message=error_message,
                timestamp=datetime.utcnow(),
            )
            
            db.add(activity)
            await db.flush()  # Flush to get the ID without committing
            
            logger.info(
                f"Activity logged: user={telegram_username or user_id} "
                f"action={activity_type.value} "
                f"resource={resource_type}/{resource_id} "
                f"status={status}"
            )
            
            return activity
        
        except Exception as e:
            logger.error(f"Failed to log activity: {e}", exc_info=True)
            # Don't raise - logging failures shouldn't break operations
            return None

    @staticmethod
    async def log_wallet_created(
        db: AsyncSession,
        user_id: UUID,
        wallet_id: UUID,
        blockchain: str,
        address: str,
        telegram_id: str = None,
        telegram_username: str = None,
    ) -> ActivityLog:
        """Log wallet creation."""
        return await ActivityService.log_activity(
            db=db,
            user_id=user_id,
            activity_type=ActivityType.WALLET_CREATED,
            description=f"Created {blockchain} wallet",
            resource_type="wallet",
            resource_id=str(wallet_id),
            metadata={"blockchain": blockchain, "address": address},
            telegram_id=telegram_id,
            telegram_username=telegram_username,
        )

    @staticmethod
    async def log_wallet_imported(
        db: AsyncSession,
        user_id: UUID,
        wallet_id: UUID,
        blockchain: str,
        address: str,
        telegram_id: str = None,
        telegram_username: str = None,
    ) -> ActivityLog:
        """Log wallet import."""
        return await ActivityService.log_activity(
            db=db,
            user_id=user_id,
            activity_type=ActivityType.WALLET_IMPORTED,
            description=f"Imported {blockchain} wallet",
            resource_type="wallet",
            resource_id=str(wallet_id),
            metadata={"blockchain": blockchain, "address": address},
            telegram_id=telegram_id,
            telegram_username=telegram_username,
        )

    @staticmethod
    async def log_wallet_set_primary(
        db: AsyncSession,
        user_id: UUID,
        wallet_id: UUID,
        blockchain: str,
        telegram_id: str = None,
        telegram_username: str = None,
    ) -> ActivityLog:
        """Log setting wallet as primary."""
        return await ActivityService.log_activity(
            db=db,
            user_id=user_id,
            activity_type=ActivityType.WALLET_SET_PRIMARY,
            description=f"Set {blockchain} wallet as primary",
            resource_type="wallet",
            resource_id=str(wallet_id),
            metadata={"blockchain": blockchain},
            telegram_id=telegram_id,
            telegram_username=telegram_username,
        )

    @staticmethod
    async def log_nft_minted(
        db: AsyncSession,
        user_id: UUID,
        nft_id: UUID,
        blockchain: str,
        name: str,
        telegram_id: str = None,
        telegram_username: str = None,
    ) -> ActivityLog:
        """Log NFT minting."""
        return await ActivityService.log_activity(
            db=db,
            user_id=user_id,
            activity_type=ActivityType.NFT_MINTED,
            description=f"Minted NFT '{name}' on {blockchain}",
            resource_type="nft",
            resource_id=str(nft_id),
            metadata={"blockchain": blockchain, "name": name},
            telegram_id=telegram_id,
            telegram_username=telegram_username,
        )

    @staticmethod
    async def log_nft_listed(
        db: AsyncSession,
        user_id: UUID,
        nft_id: UUID,
        listing_id: UUID,
        price: float,
        currency: str,
        telegram_id: str = None,
        telegram_username: str = None,
    ) -> ActivityLog:
        """Log NFT listing."""
        return await ActivityService.log_activity(
            db=db,
            user_id=user_id,
            activity_type=ActivityType.NFT_LISTED,
            description=f"Listed NFT for {price} {currency}",
            resource_type="listing",
            resource_id=str(listing_id),
            metadata={"nft_id": str(nft_id), "price": price, "currency": currency},
            telegram_id=telegram_id,
            telegram_username=telegram_username,
        )

    @staticmethod
    async def log_error(
        db: AsyncSession,
        user_id: UUID,
        activity_type: ActivityType,
        error_message: str,
        resource_type: str = None,
        resource_id: str = None,
        metadata: Dict[str, Any] = None,
        telegram_id: str = None,
        telegram_username: str = None,
    ) -> ActivityLog:
        """Log activity failure."""
        return await ActivityService.log_activity(
            db=db,
            user_id=user_id,
            activity_type=activity_type,
            description=f"Failed: {error_message[:200]}",
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata or {},
            status="failed",
            error_message=error_message,
            telegram_id=telegram_id,
            telegram_username=telegram_username,
        )
