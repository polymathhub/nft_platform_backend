"""TON Wallet integration model for GiftedForge NFT platform."""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Index, JSON, Boolean
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database.base_class import Base
from app.database.types import GUID


class TONWalletStatus(str, PyEnum):
    """Status of TON wallet connection."""
    PENDING = "pending"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"


class TONWallet(Base):
    """TON Blockchain wallet connection for users."""
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
    # TON wallet address (0x... format)
    wallet_address = Column(String(255), unique=True, nullable=False, index=True)
    
    # TON Connect connection info
    tonconnect_session_id = Column(String(255), nullable=True, unique=True)
    
    # Wallet status
    status = Column(
        Enum(TONWalletStatus),
        default=TONWalletStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    # Is this the primary wallet for marketplace transactions
    is_primary = Column(Boolean, default=True, nullable=False)
    
    # Metadata - stores wallet info from TonConnect
    wallet_metadata = Column(JSON, nullable=True, default={
        "wallet_name": None,
        "device": None,
        "last_activity": None,
    })
    
    # Timestamps
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
    """Telegram Stars transaction for marketplace purchases."""
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
    
    # Related TON wallet
    ton_wallet_id = Column(
        GUID(),
        ForeignKey("ton_wallets.id"),
        nullable=True,
        index=True,
    )
    
    # Telegram payment info
    telegram_payment_charge_id = Column(String(255), nullable=True, unique=True)
    provider_payment_charge_id = Column(String(255), nullable=True)
    
    # Transaction details
    amount_stars = Column(String(50), nullable=False)  # Amount in Telegram Stars (as string for precision)
    
    # Marketplace transaction type
    transaction_type = Column(String(50), nullable=False)  # "buy_nft", "offer", "auction"
    related_nft_id = Column(GUID(), ForeignKey("nfts.id"), nullable=True)
    related_listing_id = Column(GUID(), ForeignKey("listings.id"), nullable=True)
    related_order_id = Column(GUID(), ForeignKey("orders.id"), nullable=True)
    
    # Status
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, completed, failed, refunded
    
    # Description
    description = Column(String(255), nullable=True)
    
    # Metadata
    tx_metadata = Column(JSON, nullable=True, default={})
    
    # Timestamps
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
