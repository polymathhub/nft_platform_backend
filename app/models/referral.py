from sqlalchemy import (
    Column, String, DateTime, Boolean, Index, ForeignKey,
    Float, Integer, Enum, Text, func
)
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database.base_class import Base
from app.database.types import GUID
class ReferralStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    VERIFIED = "verified"
class CommissionStatus(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"
class Referral(Base):
    __tablename__ = "referrals"
    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    referrer_id = Column(
        GUID(),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    referred_user_id = Column(
        GUID(),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=True,
    )
    referral_code = Column(String(50), nullable=False, index=True)
    status = Column(
        Enum(ReferralStatus),
        default=ReferralStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    lifetime_earnings = Column(Float, default=0.0, nullable=False)
    referred_purchase_count = Column(Integer, default=0, nullable=False)
    referred_purchase_amount = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    first_purchase_at = Column(DateTime, nullable=True)
    locked_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    __table_args__ = (
        Index("ix_referrals_referrer_status", "referrer_id", "status"),
        Index("ix_referrals_referred_user", "referred_user_id"),
        Index("ix_referrals_code_status", "referral_code", "status"),
    )
    def __repr__(self) -> str:
        return f"<Referral(referrer={self.referrer_id}, referred={self.referred_user_id}, earnings={self.lifetime_earnings})>"
class ReferralCommission(Base):
    __tablename__ = "referral_commissions"
    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    referral_id = Column(
        GUID(),
        ForeignKey('referrals.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    transaction_id = Column(
        GUID(),
        ForeignKey('payments.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
    )
    commission_amount = Column(Float, default=0.0, nullable=False)
    commission_rate = Column(Float, default=0.1, nullable=False)
    transaction_amount = Column(Float, nullable=False)
    status = Column(
        Enum(CommissionStatus),
        default=CommissionStatus.PENDING,
        nullable=False,
        index=True,
    )
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    paid_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    __table_args__ = (
        Index("ix_referral_commissions_referral_status", "referral_id", "status"),
        Index("ix_referral_commissions_earned", "earned_at"),
    )
    def __repr__(self) -> str:
        return f"<ReferralCommission(referral={self.referral_id}, amount={self.commission_amount}, status={self.status})>"
