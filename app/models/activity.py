"""
Activity Log - Tracks all user activities for audit trail and management.
Every action by a user is logged here for accountability and history.
"""

from sqlalchemy import Column, String, DateTime, Index, JSON, ForeignKey, Enum as SQLEnum
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database import Base
from app.database.types import GUID


class ActivityType(PyEnum):
    """Activity types for audit trail."""
    # User activities
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    
    # Wallet activities
    WALLET_CREATED = "wallet_created"
    WALLET_IMPORTED = "wallet_imported"
    WALLET_DELETED = "wallet_deleted"
    WALLET_SET_PRIMARY = "wallet_set_primary"
    WALLET_UPDATED = "wallet_updated"
    
    # NFT activities
    NFT_MINTED = "nft_minted"
    NFT_BURNED = "nft_burned"
    NFT_TRANSFERRED = "nft_transferred"
    NFT_LISTED = "nft_listed"
    NFT_UNLISTED = "nft_unlisted"
    
    # Marketplace activities
    LISTING_CREATED = "listing_created"
    LISTING_CANCELLED = "listing_cancelled"
    OFFER_MADE = "offer_made"
    OFFER_ACCEPTED = "offer_accepted"
    PURCHASE_COMPLETED = "purchase_completed"
    
    # Misc activities
    API_CALL = "api_call"
    ERROR = "error"


class ActivityLog(Base):
    """
    Audit trail for all user activities.
    Links every action to the Telegram user who initiated it.
    """
    __tablename__ = "activity_logs"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    
    # Link to user
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # User identification
    telegram_id = Column(String(50), nullable=True, index=True)
    telegram_username = Column(String(100), nullable=True, index=True)
    
    # Activity details
    activity_type = Column(
        SQLEnum(ActivityType),
        nullable=False,
        index=True,
    )
    
    # Resource affected (wallet_id, nft_id, listing_id, etc.)
    resource_type = Column(String(50), nullable=True, index=True)  # e.g. "wallet", "nft", "listing"
    resource_id = Column(String(100), nullable=True, index=True)
    
    # Details about the action
    description = Column(String(500), nullable=True)
    
    # Metadata (flexible storage for additional context)
    metadata = Column(JSON, nullable=True, default={})
    
    # IP address and user agent
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Status of the activity
    status = Column(String(20), default="success", nullable=False)  # success, failed, pending
    
    # Error message if failed
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
