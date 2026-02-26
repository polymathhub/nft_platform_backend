from pydantic import BaseModel, Field, field_validator, computed_field
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from enum import Enum


class CurrencyEnum(str, Enum):
    USDT = "USDT"
    ETH = "ETH"
    SOL = "SOL"
    TON = "TON"


class ListingStatusEnum(str, Enum):
    ACTIVE = "active"
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OfferStatusEnum(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ListingRequest(BaseModel):
    nft_id: UUID
    price: float = Field(..., gt=0, le=1_000_000, description="Price in specified currency")
    currency: CurrencyEnum = Field(default=CurrencyEnum.USDT, description="Currency for listing (USDT recommended)")
    expires_at: Optional[datetime] = None
    
    @field_validator("price")
    @classmethod
    def validate_price_precision(cls, v: float) -> float:
        # Ensure price has reasonable precision (max 2 decimals for currency)
        rounded = round(v, 2)
        if abs(rounded - v) > 0.001:
            raise ValueError("Price must have at most 2 decimal places")
        return rounded


class ListingResponse(BaseModel):
    id: UUID
    nft_id: UUID
    seller_id: UUID
    seller_address: str
    price: float
    currency: str
    blockchain: str
    status: ListingStatusEnum
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    name: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class OfferRequest(BaseModel):
    listing_id: UUID
    offer_price: float = Field(..., gt=0)
    currency: str = Field(..., min_length=1, max_length=10)
    expires_at: Optional[datetime] = None


class OfferResponse(BaseModel):
    id: UUID
    listing_id: UUID
    nft_id: UUID
    buyer_id: UUID
    buyer_address: str
    offer_price: float
    currency: str
    status: OfferStatusEnum
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BuyNowRequest(BaseModel):
    listing_id: UUID
    transaction_hash: str


class AcceptOfferRequest(BaseModel):
    offer_id: UUID
    transaction_hash: str


class OrderResponse(BaseModel):
    id: UUID
    listing_id: Optional[UUID]
    offer_id: Optional[UUID]
    nft_id: UUID
    seller_id: UUID
    buyer_id: UUID
    amount: float
    currency: str
    blockchain: str
    transaction_hash: Optional[str]
    status: OrderStatusEnum
    royalty_amount: Optional[float]
    platform_fee: Optional[float]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ActiveListingsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[ListingResponse]


class UserListingsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[ListingResponse]


class ListingOffersResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[OfferResponse]


class UserOrdersResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[OrderResponse]

    
