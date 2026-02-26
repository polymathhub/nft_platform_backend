"""Referral system models for tracking referrals and commissions."""

from sqlalchemy import (
    Column, String, DateTime, Boolean, Index, ForeignKey,
    Float, Integer, Enum, Text, func
)
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database import Base
from app.database.types import GUID


class ReferralStatus(PyEnum):
    """Referral relationship status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    VERIFIED = "verified"


class CommissionStatus(PyEnum):
    """Commission/payout status."""
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


class Referral(Base):
    """Track referral relationships between users."""
    __tablename__ = "referrals"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    # The user who referred someone
    referrer_id = Column(
        GUID(),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    # The user who was referred
    referred_user_id = Column(
        GUID(),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=True,  # Each user can only be referred once
    )
    # Referral code used
    referral_code = Column(String(50), nullable=False, index=True)
    # Current status of the referral
    status = Column(
        Enum(ReferralStatus),
        default=ReferralStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    # Lifetime earnings from this referral
    lifetime_earnings = Column(Float, default=0.0, nullable=False)
    # Total purchases by referred user
    referred_purchase_count = Column(Integer, default=0, nullable=False)
    # Total purchase amount by referred user
    referred_purchase_amount = Column(Float, default=0.0, nullable=False)
    # When the referral was created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    # When the referred user first made a purchase
    first_purchase_at = Column(DateTime, nullable=True)
    # When the referral relationship was locked (no more edits allowed)
    locked_at = Column(DateTime, nullable=True)
    # Notes/metadata about the referral
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_referrals_referrer_status", "referrer_id", "status"),
        Index("ix_referrals_referred_user", "referred_user_id"),
        Index("ix_referrals_code_status", "referral_code", "status"),
    )

    def __repr__(self) -> str:
        return f"<Referral(referrer={self.referrer_id}, referred={self.referred_user_id}, earnings={self.lifetime_earnings})>"


class ReferralCommission(Base):
    """Track individual commissions earned from referral transactions."""
    __tablename__ = "referral_commissions"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    # The referral relationship this commission belongs to
    referral_id = Column(
        GUID(),
        ForeignKey('referrals.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    # The transaction that triggered this commission
    transaction_id = Column(
        GUID(),
        ForeignKey('payments.id', ondelete='CASCADE'),
        nullable=True,  # Might not have a transaction yet
        index=True,
    )
    # Amount of stars earned from this transaction
    commission_amount = Column(Float, default=0.0, nullable=False)
    # Commission rate applied (e.g., 0.1 for 10%)
    commission_rate = Column(Float, default=0.1, nullable=False)
    # Original transaction amount
    transaction_amount = Column(Float, nullable=False)
    # Status of this commission
    status = Column(
        Enum(CommissionStatus),
        default=CommissionStatus.PENDING,
        nullable=False,
        index=True,
    )
    # When this commission was earned
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    # When this commission was paid out
    paid_at = Column(DateTime, nullable=True)
    # Notes about this commission
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_referral_commissions_referral_status", "referral_id", "status"),
        Index("ix_referral_commissions_earned", "earned_at"),
    )

    def __repr__(self) -> str:
        return f"<ReferralCommission(referral={self.referral_id}, amount={self.commission_amount}, status={self.status})>"
