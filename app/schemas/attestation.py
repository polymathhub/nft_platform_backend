from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from enum import Enum


class AttestationTypeEnum(str, Enum):
    AUTHENTICITY = "authenticity"
    ROYALTY = "royalty"
    PROVENANCE = "provenance"
    RARITY = "rarity"
    VERIFICATION = "verification"


class AttestationStatusEnum(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class CreateAttestationRequest(BaseModel):
    nft_id: UUID
    attestation_type: AttestationTypeEnum = Field(...)
    score: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None
    signature: Optional[str] = None
    duration_days: Optional[int] = 365


class AttestationResponse(BaseModel):
    id: UUID
    nft_id: UUID
    attester_address: str
    attestation_type: str
    status: AttestationStatusEnum
    score: float
    metadata: Optional[Dict[str, Any]]
    signature: Optional[str]
    transaction_hash: Optional[str]
    created_at: datetime
    updated_at: datetime
    verified_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class NFTAttestationsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[AttestationResponse]


class VerifiedAttestationResponse(BaseModel):
    items: list[AttestationResponse]
    verified_count: int
    average_score: float


class AttesterHistoryResponse(BaseModel):
    total: int
    page: int
    per_page: int
    attester_address: str
    items: list[AttestationResponse]
