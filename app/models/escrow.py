from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Float, JSON
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database import Base
from app.database.types import GUID


class EscrowStatus(str, PyEnum):
    PENDING = "pending"
    HELD = "held"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class Escrow(Base):
    __tablename__ = "escrows"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    listing_id = Column(GUID(), ForeignKey("listings.id", ondelete="CASCADE"), nullable=True, index=True)
    offer_id = Column(GUID(), ForeignKey("offers.id", ondelete="CASCADE"), nullable=True, index=True)
    order_id = Column(GUID(), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    buyer_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(50), nullable=False)
    commission_amount = Column(Float, nullable=True, default=0.0)
    status = Column(Enum(EscrowStatus), default=EscrowStatus.PENDING, nullable=False)
    escrow_metadata = Column(JSON, nullable=True, default={})
    tx_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Escrow(id={self.id}, offer_id={self.offer_id}, amount={self.amount}, status={self.status})>"
