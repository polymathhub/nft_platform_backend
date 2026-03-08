"""
Notification Model - User notifications for real-time events.
Stores notification history and user notification preferences.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Index, ForeignKey, Enum as SQLEnum, Text
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database import Base
from app.database.types import GUID


class NotificationType(PyEnum):
    """Notification type enumeration."""
    # NFT Events
    NFT_MINTED = "nft_minted"
    NFT_SOLD = "nft_sold"
    NFT_PURCHASED = "nft_purchased"
    NFT_LISTED = "nft_listed"
    NFT_OFFER_RECEIVED = "nft_offer_received"
    NFT_OFFER_ACCEPTED = "nft_offer_accepted"
    
    # Marketplace Events
    LISTING_SOLD = "listing_sold"
    OFFER_MADE = "offer_made"
    OFFER_ACCEPTED = "offer_accepted"
    
    # System Events
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_PENDING = "payment_pending"
    REFERRAL_EARNED = "referral_earned"
    
    # User Events
    ACCOUNT_VERIFIED = "account_verified"
    ACCOUNT_WARNING = "account_warning"
    PASSWORD_CHANGED = "password_changed"
    
    # General
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class Notification(Base):
    """
    User notifications table.
    Stores all notifications sent to users.
    """
    __tablename__ = "notifications"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    
    # User reference
    user_id = Column(
        GUID(),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    
    # Notification data
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    message = Column(Text, nullable=True)  # Alias for description
    subject = Column(String(255), nullable=True)  # Alias for title
    
    # Notification type
    notification_type = Column(
        SQLEnum(NotificationType),
        default=NotificationType.INFO,
        nullable=False,
        index=True,
    )
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read = Column(Boolean, default=False, nullable=False)  # Alias for is_read
    
    # Link/action
    action_url = Column(String(500), nullable=True)
    action_type = Column(String(50), nullable=True)  # e.g., "view_nft", "accept_offer"
    
    # Metadata
    metadata = Column(String(1000), nullable=True)  # JSON string for extra data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)
    
    # Expiration (optional - delete old notifications)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_id_created_at', 'user_id', 'created_at'),
        Index('idx_user_id_is_read', 'user_id', 'is_read'),
    )
