from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from uuid import UUID


class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    blockchain: str
    contract_address: Optional[str] = None
    rarity_weights: Optional[Dict[str, float]] = None
    image_url: Optional[str] = None
    banner_url: Optional[str] = None


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rarity_weights: Optional[Dict[str, float]] = None
    image_url: Optional[str] = None
    banner_url: Optional[str] = None


class CollectionStats(BaseModel):
    id: str
    name: str
    floor_price: Optional[float] = None
    average_price: Optional[float] = None
    ceiling_price: Optional[float] = None
    total_volume: float
    total_sales: int


class CollectionResponse(CollectionBase):
    id: UUID
    creator_id: UUID
    floor_price: Optional[float] = None
    average_price: Optional[float] = None
    ceiling_price: Optional[float] = None
    total_volume: float
    total_sales: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NFTRarity(BaseModel):
    rarity_score: Optional[float] = None
    rarity_tier: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None


class NFTValuation(BaseModel):
    nft_id: str
    name: str
    rarity_score: Optional[float] = None
    rarity_tier: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None
    suggested_price: Optional[float] = None
    collection_floor_price: Optional[float] = None
    collection_average_price: Optional[float] = None


class ListingWithRarity(BaseModel):
    id: UUID
    nft_id: UUID
    seller_id: UUID
    seller_address: str
    price: float
    currency: str
    blockchain: str
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    nft_name: Optional[str] = None
    rarity_tier: Optional[str] = None
    rarity_score: Optional[float] = None
    attributes: Optional[Dict[str, str]] = None

    class Config:
        from_attributes = True


class PriceSuggestion(BaseModel):
    nft_id: str
    suggested_price: Optional[float]
    floor_price: Optional[float] = None
    average_market_price: Optional[float] = None
    confidence: Optional[str] = None  # 'high', 'medium', 'low'
