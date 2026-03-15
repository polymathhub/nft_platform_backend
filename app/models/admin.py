from sqlalchemy import Column, String, DateTime, Text, Enum, DECIMAL, Index
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database.base_class import Base
from app.database.types import GUID
class AdminLogAction(PyEnum):
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
    __tablename__ = "admin_logs"
    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    admin_id = Column(GUID(), nullable=False, index=True)
    action = Column(Enum(AdminLogAction), nullable=False, index=True)
    target_user_id = Column(GUID(), nullable=True, index=True)
    target_resource_id = Column(String(255), nullable=True, index=True)
    resource_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (
        Index("ix_admin_logs_admin_action", "admin_id", "action"),
    )
    def __repr__(self) -> str:
        return f"<AdminLog(id={self.id}, admin_id={self.admin_id}, action={self.action})>"
class AdminSettings(Base):
    __tablename__ = "admin_settings"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    commission_rate = Column(DECIMAL(5, 2), default=2.0, nullable=False)
    commission_wallet = Column(String(255), nullable=False)
    commission_blockchain = Column(String(50), nullable=False, default="ethereum")
    min_listing_price = Column(DECIMAL(10, 2), default=0.01, nullable=False)
    max_listing_price = Column(DECIMAL(20, 2), default=1000000.00, nullable=False)
    enable_marketplace = Column(String(5), default="true", nullable=False)
    enable_nft_minting = Column(String(5), default="true", nullable=False)
    enable_telegram = Column(String(5), default="true", nullable=False)
    last_backup_at = Column(DateTime, nullable=True)
    last_backup_hash = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(GUID(), nullable=True)
    __table_args__ = (
        Index("ix_admin_settings_updated_at", "updated_at"),
    )
    def __repr__(self) -> str:
        return f"<AdminSettings(id={self.id}, commission_rate={self.commission_rate})>"
