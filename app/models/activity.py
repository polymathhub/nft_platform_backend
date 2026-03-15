from sqlalchemy import Column, String, DateTime, Index, JSON, ForeignKey, Enum as SQLEnum
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database.base_class import Base
from app.database.types import GUID
class ActivityType(PyEnum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    WALLET_CREATED = "wallet_created"
    WALLET_IMPORTED = "wallet_imported"
    WALLET_DELETED = "wallet_deleted"
    WALLET_SET_PRIMARY = "wallet_set_primary"
    WALLET_UPDATED = "wallet_updated"
    NFT_MINTED = "nft_minted"
    NFT_BURNED = "nft_burned"
    NFT_TRANSFERRED = "nft_transferred"
    NFT_LISTED = "nft_listed"
    NFT_UNLISTED = "nft_unlisted"
    LISTING_CREATED = "listing_created"
    LISTING_CANCELLED = "listing_cancelled"
    OFFER_MADE = "offer_made"
    OFFER_ACCEPTED = "offer_accepted"
    PURCHASE_COMPLETED = "purchase_completed"
    API_CALL = "api_call"
    ERROR = "error"
class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    telegram_id = Column(String(50), nullable=True, index=True)
    telegram_username = Column(String(100), nullable=True, index=True)
    activity_type = Column(
        SQLEnum(ActivityType),
        nullable=False,
        index=True,
    )
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(100), nullable=True, index=True)
    description = Column(String(500), nullable=True)
    activity_metadata = Column(JSON, nullable=True, default={})
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), default="success", nullable=False)
    error_message = Column(String(500), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (
        Index("ix_activity_user_timestamp", "user_id", "timestamp"),
        Index("ix_activity_telegram_timestamp", "telegram_id", "timestamp"),
        Index("ix_activity_type_timestamp", "activity_type", "timestamp"),
        Index("ix_activity_resource", "resource_type", "resource_id"),
    )
    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, user_id={self.user_id}, activity={self.activity_type}, timestamp={self.timestamp})>"
