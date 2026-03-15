from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Index, Text, Float
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database.base_class import Base
from app.database.types import GUID
class PaymentType(str, PyEnum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"
class Payment(Base):
    __tablename__ = "payments"
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
    wallet_id = Column(
        GUID(),
        ForeignKey("wallets.id"),
        nullable=False,
        index=True,
    )
    payment_type = Column(
        Enum(PaymentType),
        nullable=False,
        index=True,
    )
    status = Column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    blockchain = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(20), default="USDT", nullable=False)
    counterparty_address = Column(String(255), nullable=True)
    transaction_hash = Column(String(255), nullable=True, unique=True)
    transaction_hash_external = Column(String(255), nullable=True)
    network_fee = Column(Float, nullable=True)
    platform_fee = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    __table_args__ = (
        Index("ix_payments_user_type_status", "user_id", "payment_type", "status"),
        Index("ix_payments_wallet_type", "wallet_id", "payment_type"),
        Index("ix_payments_blockchain_hash", "blockchain", "transaction_hash"),
    )
    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, user_id={self.user_id}, type={self.payment_type}, status={self.status}, amount={self.amount})>"
