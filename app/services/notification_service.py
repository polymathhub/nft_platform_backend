import logging
import json
import uuid
from typing import Set, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):

    NFT_MINTED = "nft_minted"
    NFT_TRANSFERRED = "nft_transferred"
    NFT_BURNED = "nft_burned"
    TRANSACTION_CONFIRMED = "transaction_confirmed"
    TRANSACTION_FAILED = "transaction_failed"
    WALLET_CREATED = "wallet_created"
    SYSTEM_MESSAGE = "system_message"


class Notification:

    def __init__(
        self,
        notification_type: NotificationType,
        user_id: UUID,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        self.id = str(uuid.uuid4())
        self.type = notification_type
        self.user_id = user_id
        self.title = title
        self.message = message
        self.data = data or {}
        self.created_at = datetime.utcnow()
        self.read = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "user_id": str(self.user_id),
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "read": self.read,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class NotificationService:

    # In-memory store of active connections (user_id set of websocket connections)
    active_connections: Dict[UUID, Set[Any]] = {}

    @classmethod
    async def connect(cls, user_id: UUID, websocket: Any) -> None:
        if user_id not in cls.active_connections:
            cls.active_connections[user_id] = set()
        cls.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Active: {len(cls.active_connections[user_id])}")

    @classmethod
    async def disconnect(cls, user_id: UUID, websocket: Any) -> None:
        if user_id in cls.active_connections:
            cls.active_connections[user_id].discard(websocket)
            if not cls.active_connections[user_id]:
                del cls.active_connections[user_id]
            logger.info(
                f"User {user_id} disconnected. Active: {len(cls.active_connections.get(user_id, set()))}"
            )

    @classmethod
    async def send_notification(
        cls,
        user_id: UUID,
        notification: Notification,
    ) -> None:
        if user_id not in cls.active_connections:
            logger.debug(f"User {user_id} has no active connections")
            return

        disconnected = []
        for websocket in cls.active_connections[user_id]:
            try:
                await websocket.send_json(notification.to_dict())
                logger.debug(f"Notification sent to {user_id}")
            except Exception as e:
                logger.error(f"Error sending notification to {user_id}: {e}")
                disconnected.append(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            cls.active_connections[user_id].discard(websocket)

    @classmethod
    async def broadcast_to_all(cls, notification: Notification) -> None:
        for user_id in list(cls.active_connections.keys()):
            await cls.send_notification(user_id, notification)

    @classmethod
    async def notify_nft_minted(
        cls,
        user_id: UUID,
        nft_name: str,
        nft_id: str,
        contract_address: str,
        token_id: str,
    ) -> None:
        """Notify user about minted NFT."""
        notification = Notification(
            notification_type=NotificationType.NFT_MINTED,
            user_id=user_id,
            title="NFT Minted Successfully",
            message=f"Your NFT '{nft_name}' has been minted!",
            data={
                "nft_id": nft_id,
                "nft_name": nft_name,
                "contract_address": contract_address,
                "token_id": token_id,
            },
        )
        await cls.send_notification(user_id, notification)

    @classmethod
    async def notify_nft_transferred(
        cls,
        user_id: UUID,
        nft_name: str,
        to_address: str,
        nft_id: str,
    ) -> None:
        
        """Notify user about transferred NFT."""
        notification = Notification(
            notification_type=NotificationType.NFT_TRANSFERRED,
            user_id=user_id,
            title="NFT Transferred",
            message=f"Your NFT '{nft_name}' has been transferred to {to_address[:16]}...",
            data={
                "nft_id": nft_id,
                "nft_name": nft_name,
                "to_address": to_address,
            },
        )
        await cls.send_notification(user_id, notification)

    @classmethod
    async def notify_transaction_confirmed(
        cls,
        user_id: UUID,
        tx_hash: str,
        action: str,
    ) -> None:
        
        """Notify user about confirmed transaction."""
        notification = Notification(
            notification_type=NotificationType.TRANSACTION_CONFIRMED,
            user_id=user_id,
            title="Transaction Confirmed",
            message=f"Your {action} transaction has been confirmed!",
            data={
                "tx_hash": tx_hash,
                "action": action,
            },
        )
        await cls.send_notification(user_id, notification)

    @classmethod
    async def notify_transaction_failed(
        cls,
        user_id: UUID,
        tx_hash: str,
        action: str,
        error: str,
    ) -> None:

        """Notify user about failed transaction."""
        notification = Notification(
            notification_type=NotificationType.TRANSACTION_FAILED,
            user_id=user_id,
            title="Transaction Failed",
            message=f"Your {action} transaction failed: {error}",
            data={
                "tx_hash": tx_hash,
                "action": action,
                "error": error,
            },
        )
        await cls.send_notification(user_id, notification)

    @classmethod
    def get_active_users(cls) -> int:
        return len(cls.active_connections)
    @classmethod
    async def send_telegram_notification(
        cls,
        user: Any,  # User model
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send notification via Telegram if user has linked account."""
        if not user or not user.telegram_id:
            logger.debug(f"User {user.id if user else 'Unknown'} has no Telegram ID")
            return False

        try:
            from app.services.telegram_bot_service import TelegramBotService
            bot = TelegramBotService()
            return await bot.send_notification(user, title, message, data)
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return False

    @classmethod
    async def notify_nft_minted_telegram(
        cls,
        user: Any,  # User model
        nft_name: str,
        nft_id: str,
        contract_address: Optional[str] = None,
        token_id: Optional[str] = None,
    ) -> None:
        """Send Telegram notification about minted NFT."""
        message = f"Your NFT <b>{nft_name}</b> has been successfully minted!"
        data = {
            "nft_id": nft_id,
            "nft_name": nft_name,
        }
        if contract_address:
            data["contract"] = contract_address[:16] + "..."
        if token_id:
            data["token_id"] = token_id

        await cls.send_telegram_notification(
            user=user,
            title="🎉 NFT Minted Successfully",
            message=message,
            data=data,
        )

    @classmethod
    async def notify_nft_transferred_telegram(
        cls,
        user: Any,  # User model
        nft_name: str,
        to_address: str,
        nft_id: str,
    ) -> None:
        """Send Telegram notification about transferred NFT."""
        message = f"Your NFT <b>{nft_name}</b> has been transferred."
        await cls.send_telegram_notification(
            user=user,
            title="↔️ NFT Transferred",
            message=message,
            data={
                "nft_id": nft_id,
                "to_address": to_address[:16] + "...",
            },
        )

    @classmethod
    async def notify_transaction_confirmed_telegram(
        cls,
        user: Any,  # User model
        tx_hash: str,
        action: str,
    ) -> None:
        """Send Telegram notification about confirmed transaction."""
        message = f"Your <b>{action}</b> transaction has been confirmed!"
        await cls.send_telegram_notification(
            user=user,
            title="✅ Transaction Confirmed",
            message=message,
            data={"tx_hash": tx_hash[:16] + "..."},
        )

    @classmethod
    async def notify_transaction_failed_telegram(
        cls,
        user: Any,  # User model
        tx_hash: str,
        action: str,
        error: str,
    ) -> None:
        """Send Telegram notification about failed transaction."""
        message = f"Your <b>{action}</b> transaction failed.\n\nError: {error}"
        await cls.send_telegram_notification(
            user=user,
            title="❌ Transaction Failed",
            message=message,
            data={"tx_hash": tx_hash[:16] + "..." if tx_hash else "N/A"},
        )

    @classmethod
    async def notify_nft_listed_telegram(
        cls,
        user: Any,  # User model
        nft_name: str,
        price: float,
        currency: str,
        listing_id: str,
    ) -> None:
        """Send Telegram notification about NFT listing."""
        message = f"Your NFT <b>{nft_name}</b> is now listed on marketplace."
        await cls.send_telegram_notification(
            user=user,
            title="📢 NFT Listed",
            message=message,
            data={
                "listing_id": listing_id[:16] + "...",
                "price": f"{price} {currency}",
            },
        )

    @classmethod
    async def notify_offer_received_telegram(
        cls,
        user: Any,  # User model
        nft_name: str,
        offer_price: float,
        currency: str,
        from_user: str,
        offer_id: str,
    ) -> None:
        """Send Telegram notification about received offer."""
        message = f"You received an offer for <b>{nft_name}</b> worth <code>{offer_price} {currency}</code> from {from_user}."
        await cls.send_telegram_notification(
            user=user,
            title="💰 New Offer",
            message=message,
            data={
                "offer_id": offer_id[:16] + "...",
                "price": f"{offer_price} {currency}",
            },
        )

    @classmethod
    async def notify_listing_cancelled_telegram(
        cls,
        user: Any,  # User model
        nft_name: str,
        listing_id: str,
    ) -> None:
        """Send Telegram notification about cancelled listing."""
        message = f"Your NFT <b>{nft_name}</b> listing has been cancelled."
        await cls.send_telegram_notification(
            user=user,
            title="❌ Listing Cancelled",
            message=message,
            data={"listing_id": listing_id[:16] + "..."},
        )

    @classmethod
    async def notify_nft_burned_telegram(
        cls,
        user: Any,  # User model
        nft_name: str,
        nft_id: str,
    ) -> None:
        """Send Telegram notification about burned NFT."""
        message = f"Your NFT <b>{nft_name}</b> has been burned."
        await cls.send_telegram_notification(
            user=user,
            title="🔥 NFT Burned",
            message=message,
            data={"nft_id": nft_id[:16] + "..."},
        )