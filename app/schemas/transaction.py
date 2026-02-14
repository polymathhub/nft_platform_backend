from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from enum import Enum


class TransactionTypeEnum(str, Enum):
    MINT = "mint"
    TRANSFER = "transfer"
    BURN = "burn"
    BRIDGE = "bridge"

class TransactionStatusEnum(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class TransactionResponse(BaseModel):
    id: UUID
    transaction_type: TransactionTypeEnum
    blockchain: str
    from_address: str
    to_address: str
    transaction_hash: Optional[str]
    status: TransactionStatusEnum
    gas_fee: Optional[float]
    gas_currency: Optional[str]
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TransactionDetailResponse(TransactionResponse):
    user_id: UUID
    nft_id: Optional[UUID]
    wallet_id: UUID


class TransactionListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[TransactionResponse]
