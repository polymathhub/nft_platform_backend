from sqlalchemy import Column, String, DateTime, Text, Enum, DECIMAL, Index
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database import Base
from app.database.types import GUID


class AdminLogAction(PyEnum):
    """Admin action types for audit logging."""
    USER_ROLE_CHANGED = "user_role_changed"
    COMMISSION_RATE_UPDATED = "commission_rate_updated"
    COMMISSION_WALLET_UPDATED = "commission_wallet_updated"
    ADMIN_ADDED = "admin_added"
    ADMIN_REMOVED = "admin_removed"
    USER_SUSPENDED = "user_suspended"
    USER_ACTIVATED = "user_activated"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    DATABASE_BACKUP = "database_backup"
    LISTING_REMOVED = "listing_removed"
    OFFER_CANCELLED = "offer_cancelled"
    NFT_LOCKED = "nft_locked"


class AdminLog(Base):
    """Admin action audit log for compliance and troubleshooting."""
    __tablename__ = "admin_logs"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    admin_id = Column(GUID(), nullable=False, index=True)  # Admin user who performed action
    action = Column(Enum(AdminLogAction), nullable=False, index=True)
    target_user_id = Column(GUID(), nullable=True, index=True)  # Optional: user being affected
    target_resource_id = Column(String(255), nullable=True, index=True)  # Optional: resource ID (listing, offer, etc)
    resource_type = Column(String(50), nullable=True)  # Optional: type of resource (listing, offer, user, etc)
    description = Column(Text, nullable=True)  # Human-readable description of action
    old_value = Column(Text, nullable=True)  # Old value if editing (JSON string)
    new_value = Column(Text, nullable=True)  # New value if editing (JSON string)
    ip_address = Column(String(50), nullable=True)  # Admin IP address for security
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_admin_logs_admin_action", "admin_id", "action"),
        # created_at index removed — created_at queries rely on table scan or other indexes
    )

    def __repr__(self) -> str:
        return f"<AdminLog(id={self.id}, admin_id={self.admin_id}, action={self.action})>"


class AdminSettings(Base):
    """System-wide admin settings (singleton)."""
    __tablename__ = "admin_settings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    # Commission settings
    commission_rate = Column(DECIMAL(5, 2), default=2.0, nullable=False)  # 2% default
    commission_wallet = Column(String(255), nullable=False)  # Wallet address to receive commissions
    commission_blockchain = Column(String(50), nullable=False, default="ethereum")  # Blockchain for commission wallet
    
    # Settings
    min_listing_price = Column(DECIMAL(10, 2), default=0.01, nullable=False)
    max_listing_price = Column(DECIMAL(20, 2), default=1000000.00, nullable=False)
    
    # Marketplace settings
    enable_marketplace = Column(String(5), default="true", nullable=False)  # "true"/"false"
    enable_nft_minting = Column(String(5), default="true", nullable=False)
    enable_telegram = Column(String(5), default="true", nullable=False)
    
    # Backup info
    last_backup_at = Column(DateTime, nullable=True)
    last_backup_hash = Column(String(255), nullable=True)  # SHA256 hash of backup
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(GUID(), nullable=True)  # Admin who made the change

    __table_args__ = (
        Index("ix_admin_settings_updated_at", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<AdminSettings(id={self.id}, commission_rate={self.commission_rate})>"
