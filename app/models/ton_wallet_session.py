"""
Production-Grade TON Wallet Session Tracking

Handles:
- Multi-device wallet sessions
- Session verification and security
- Public key storage for off-chain verification
- Device fingerprinting
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Index, JSON, Boolean, Integer
from datetime import datetime
import uuid
from app.database.base_class import Base
from app.database.types import GUID


class TONWalletSession(Base):
    """Track active wallet sessions with device info and security"""
    
    __tablename__ = "ton_wallet_sessions"
    
    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    
    # Link to TON wallet
    ton_wallet_id = Column(
        GUID(),
        ForeignKey("ton_wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Link to user
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # CRITICAL: Wallet public key for off-chain verification
    public_key = Column(
        String(255),
        nullable=False,
        index=True,
    )
    
    # Session verification
    session_hash = Column(
        String(255),
        nullable=False,
        index=True,
        unique=True,
    )
    
    # Device tracking
    device_platform = Column(
        String(50),
        nullable=True,
        default="web"  # web, ios, android
    )
    
    device_name = Column(
        String(255),
        nullable=True,
    )
    
    app_name = Column(
        String(100),
        nullable=True,
        default="tonconnect-ui"
    )
    
    # Session metadata
    device_info = Column(
        JSON,
        nullable=True,
        default={
            "user_agent": None,
            "ip_address": None,
            "country": None,
        }
    )
    
    # Activity tracking
    last_activity_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    transaction_count = Column(
        Integer,
        default=0,
        nullable=False,
    )
    
    # Session state
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    
    expires_at = Column(
        DateTime,
        nullable=True,
    )
    
    revoked_at = Column(
        DateTime,
        nullable=True,
    )
    
    __table_args__ = (
        Index("ix_ton_wallet_sessions_wallet", "ton_wallet_id", "is_active"),
        Index("ix_ton_wallet_sessions_user", "user_id", "is_active"),
        Index("ix_ton_wallet_sessions_public_key", "public_key"),
        Index("ix_ton_wallet_sessions_device", "device_platform", "device_name"),
    )
    
    def __repr__(self) -> str:
        return f"<TONWalletSession(id={self.id}, device={self.device_platform}, active={self.is_active})>"
