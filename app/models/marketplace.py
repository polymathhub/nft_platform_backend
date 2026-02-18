from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Index, Text, Float, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database import Base
from app.database.types import GUID


class ListingStatus(str, PyEnum):
    ACTIVE = "active"
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OfferStatus(str, PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrderStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Listing(Base):
    __tablename__ = "listings"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    nft_id = Column(
        GUID(),
        ForeignKey("nfts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_address = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(50), nullable=False)
    blockchain = Column(String(50), nullable=False)
    status = Column(
        Enum(ListingStatus),
        default=ListingStatus.ACTIVE,
        nullable=False,
    )
    expires_at = Column(DateTime, nullable=True)
    listing_metadata = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    nft = relationship("NFT", foreign_keys=[nft_id], lazy="select")
    seller = relationship("User", foreign_keys=[seller_id], lazy="select")

    __table_args__ = (
        Index("ix_listings_status", "status"),
        Index("ix_listings_blockchain", "blockchain"),
    )

    def __repr__(self) -> str:
        return f"<Listing(id={self.id}, nft_id={self.nft_id}, price={self.price}, status={self.status})>"


class Offer(Base):
    __tablename__ = "offers"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    listing_id = Column(
        GUID(),
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nft_id = Column(
        GUID(),
        ForeignKey("nfts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    buyer_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    buyer_address = Column(String(255), nullable=False)
    offer_price = Column(Float, nullable=False)
    currency = Column(String(50), nullable=False)
    status = Column(
        Enum(OfferStatus),
        default=OfferStatus.PENDING,
        nullable=False,
    )
    expires_at = Column(DateTime, nullable=True)
    offer_metadata = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    listing = relationship("Listing", foreign_keys=[listing_id], lazy="select")
    nft = relationship("NFT", foreign_keys=[nft_id], lazy="select")
    buyer = relationship("User", foreign_keys=[buyer_id], lazy="select")

    __table_args__ = (
        Index("ix_offers_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Offer(id={self.id}, listing_id={self.listing_id}, offer_price={self.offer_price})>"


class Order(Base):
    __tablename__ = "orders"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    listing_id = Column(
        GUID(),
        ForeignKey("listings.id"),
        nullable=True,
        index=True,
    )
    offer_id = Column(
        GUID(),
        ForeignKey("offers.id"),
        nullable=True,
        index=True,
    )
    nft_id = Column(
        GUID(),
        ForeignKey("nfts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id = Column(
        GUID(),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    buyer_id = Column(
        GUID(),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    amount = Column(Float, nullable=False)
    currency = Column(String(50), nullable=False)
    blockchain = Column(String(50), nullable=False)
    transaction_hash = Column(String(255), nullable=True, unique=True)
    status = Column(
        Enum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
    )
    royalty_amount = Column(Float, nullable=True, default=0.0)
    platform_fee = Column(Float, nullable=True, default=0.0)
    order_metadata = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    listing = relationship("Listing", foreign_keys=[listing_id], lazy="select")
    offer = relationship("Offer", foreign_keys=[offer_id], lazy="select")
    nft = relationship("NFT", foreign_keys=[nft_id], lazy="select")
    seller = relationship("User", foreign_keys=[seller_id], lazy="select", viewonly=True)
    buyer = relationship("User", foreign_keys=[buyer_id], lazy="select", viewonly=True)

    __table_args__ = (
        Index("ix_orders_status", "status"),
        Index("ix_orders_blockchain", "blockchain"),
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, nft_id={self.nft_id}, amount={self.amount}, status={self.status})>"
