from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Enum, Text, Float, JSON
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database import Base
from app.database.types import GUID


class TransactionType(str, PyEnum):

    MINT = "mint"
    TRANSFER = "transfer"
    BURN = "burn"
    BRIDGE = "bridge"


class TransactionStatus(str, PyEnum):

    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Transaction(Base):

    __tablename__ = "transactions"

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
    nft_id = Column(
        GUID(),
        ForeignKey("nfts.id"),
        nullable=True,
        index=True,
    )
    wallet_id = Column(
        GUID(),
        ForeignKey("wallets.id"),
        nullable=False,
        index=True,
    )
    transaction_type = Column(
        Enum(TransactionType),
        nullable=False,
    )
    blockchain = Column(String(50), nullable=False)
    from_address = Column(String(255), nullable=False)
    to_address = Column(String(255), nullable=False)
    transaction_hash = Column(String(255), unique=True, nullable=True)
    status = Column(
        Enum(TransactionStatus),
        default=TransactionStatus.PENDING,
        nullable=False,
    )
    gas_fee = Column(Float, nullable=True)
    gas_currency = Column(String(50), nullable=True)
    execution_fee = Column(Float, nullable=True)
    block_number = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    transaction_metadata = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_transactions_user_blockchain", "user_id", "blockchain"),
        Index("ix_transactions_nft_status", "nft_id", "status"),
        Index("ix_transactions_hash", "transaction_hash"),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, type={self.transaction_type}, status={self.status}, hash={self.transaction_hash})>"
