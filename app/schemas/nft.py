from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from enum import Enum


class BlockchainEnum(str, Enum):
    TON = "ton"
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    BITCOIN = "bitcoin"
    AVALANCHE = "avalanche"
    
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"


class NFTStatusEnum(str, Enum):
    PENDING = "pending"
    MINTED = "minted"
    TRANSFERRED = "transferred"
    LOCKED = "locked"
    BURNED = "burned"


class RarityTierEnum(str, Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class MintNFTRequest(BaseModel):
    wallet_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=500)
    royalty_percentage: int = Field(0, ge=0, le=100)
    metadata: Optional[Dict[str, Any]] = None
    collection_id: Optional[UUID] = None
    attributes: Optional[Dict[str, str]] = None


class TransferNFTRequest(BaseModel):
    to_address: str
    blockchain: BlockchainEnum
    transaction_hash: Optional[str] = Field(None, max_length=255)


class LockNFTRequest(BaseModel):
    reason: str = Field(default="marketplace", min_length=1, max_length=50)
    duration_hours: Optional[int] = Field(None, ge=1)


class UnlockNFTRequest(BaseModel):
    pass


class NFTResponse(BaseModel):
    id: UUID
    global_nft_id: str
    name: str
    description: Optional[str]
    blockchain: str
    contract_address: Optional[str]
    token_id: Optional[str]
    owner_address: str
    status: NFTStatusEnum
    is_locked: bool
    lock_reason: Optional[str]
    locked_until: Optional[datetime]
    ipfs_hash: Optional[str]
    image_url: Optional[str]
    media_type: Optional[str]
    royalty_percentage: int
    
    # Rarity info
    collection_id: Optional[UUID] = None
    attributes: Optional[Dict[str, str]] = None
    rarity_score: Optional[float] = None
    rarity_tier: Optional[RarityTierEnum] = None
    
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    minted_at: Optional[datetime]

    class Config:
        from_attributes = True


class NFTDetailResponse(NFTResponse):
    user_id: UUID
    wallet_id: UUID
    transaction_hash: Optional[str]


# ==================== WebApp Specific Requests ====================

class WebAppMintNFTRequest(BaseModel):
    """Request model for /web-app/mint endpoint"""
    wallet_id: UUID
    nft_name: str = Field(..., min_length=1, max_length=255)
    nft_description: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=500)
    user_id: UUID
    init_data: Optional[str] = None


class WebAppListNFTRequest(BaseModel):
    """Request model for /web-app/list-nft endpoint"""
    nft_id: UUID
    price: float = Field(..., gt=0)
    currency: str = Field("USDT", max_length=10)
    user_id: UUID
    init_data: Optional[str] = None


class WebAppTransferNFTRequest(BaseModel):
    """Request model for /web-app/transfer endpoint"""
    nft_id: UUID
    to_address: str = Field(..., min_length=1, max_length=255)
    user_id: UUID
    init_data: Optional[str] = None


class WebAppBurnNFTRequest(BaseModel):
    """Request model for /web-app/burn endpoint"""
    nft_id: UUID
    user_id: UUID
    init_data: Optional[str] = None


class WebAppSetPrimaryWalletRequest(BaseModel):
    """Request model for /web-app/set-primary endpoint"""
    wallet_id: UUID
    user_id: UUID
    init_data: Optional[str] = None


class WebAppMakeOfferRequest(BaseModel):
    """Request model for /web-app/make-offer endpoint"""
    listing_id: UUID
    offer_price: float = Field(..., gt=0)
    user_id: UUID
    init_data: Optional[str] = None


class WebAppCancelListingRequest(BaseModel):
    """Request model for /web-app/cancel-listing endpoint"""
    listing_id: UUID
    user_id: UUID
    init_data: Optional[str] = None


class UserNFTListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[NFTResponse]


class NFTMetadataUploadResponse(BaseModel):
    ipfs_hash: str
    ipfs_url: str
    gateway_url: str
