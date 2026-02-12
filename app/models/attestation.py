from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Text, Boolean, JSON, Float
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database import Base
from app.database.types import GUID


class AttestationType(str, PyEnum):
    AUTHENTICITY = "authenticity"
    ROYALTY = "royalty"
    PROVENANCE = "provenance"
    RARITY = "rarity"
    VERIFICATION = "verification"


class AttestationStatus(str, PyEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Attestation(Base):
    __tablename__ = "attestations"

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
    attester_address = Column(String(255), nullable=False)
    attestation_type = Column(
        String(50),
        nullable=False,
        index=True,
    )
    status = Column(
        String(50),
        default=AttestationStatus.PENDING,
        nullable=False,
        index=True,
    )
    score = Column(Float, nullable=True, default=0.0)
    attestation_metadata = Column(JSON, nullable=True, default={})
    signature = Column(String(255), nullable=True)
    transaction_hash = Column(String(255), nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_attestations_type_status", "attestation_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<Attestation(id={self.id}, nft_id={self.nft_id}, type={self.attestation_type}, status={self.status})>"
