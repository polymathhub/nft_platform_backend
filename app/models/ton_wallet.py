from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Index, JSON, Boolean
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database.base_class import Base
from app.database.types import GUID
class TONWalletStatus(str, PyEnum):
    PENDING = "pending"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
class TONWallet(Base):
    __tablename__ = "ton_wallets"
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
    wallet_address = Column(String(255), unique=True, nullable=False, index=True)
    tonconnect_session_id = Column(String(255), nullable=True, unique=True)
    status = Column(
        Enum(TONWalletStatus),
        default=TONWalletStatus.PENDING,
        nullable=False,
        index=True,
    )
    is_primary = Column(Boolean, default=True, nullable=False)
    wallet_metadata = Column(JSON, nullable=True, default={
        "wallet_name": None,
        "device": None,
        "last_activity": None,
    })
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    connected_at = Column(DateTime, nullable=True)
    disconnected_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    __table_args__ = (
        Index("ix_ton_wallets_user_status", "user_id", "status"),
        Index("ix_ton_wallets_address", "wallet_address"),
    )
    def __repr__(self) -> str:
        return f"<TONWallet(id={self.id}, user_id={self.user_id}, address={self.wallet_address}, status={self.status})>"
class StarTransaction(Base):
    __tablename__ = "star_transactions"
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
    ton_wallet_id = Column(
        GUID(),
        ForeignKey("ton_wallets.id"),
        nullable=True,
        index=True,
    )
    telegram_payment_charge_id = Column(String(255), nullable=True, unique=True)
    provider_payment_charge_id = Column(String(255), nullable=True)
    amount_stars = Column(String(50), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    related_nft_id = Column(GUID(), ForeignKey("nfts.id"), nullable=True)
    related_listing_id = Column(GUID(), ForeignKey("listings.id"), nullable=True)
    related_order_id = Column(GUID(), ForeignKey("orders.id"), nullable=True)
    status = Column(String(50), default="pending", nullable=False, index=True)
    description = Column(String(255), nullable=True)
    tx_metadata = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    __table_args__ = (
        Index("ix_star_transactions_user_status", "user_id", "status"),
        Index("ix_star_transactions_telegram_id", "telegram_payment_charge_id"),
        Index("ix_star_transactions_nft", "related_nft_id"),
    )
    def __repr__(self) -> str:
        return f"<StarTransaction(id={self.id}, user_id={self.user_id}, amount={self.amount_stars}, status={self.status})>"
