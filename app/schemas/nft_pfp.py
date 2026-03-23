"""
NFT Profile Picture (PFP) Schemas

Schemas for setting, managing, and retrieving NFT profile pictures
similar to how Twitter and other platforms handle NFT PFPs.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class NFTPFPResponse(BaseModel):
    """Response model for NFT PFP information"""
    id: UUID = Field(..., description="NFT ID being used as PFP")
    name: str = Field(..., description="NFT name")
    image_url: Optional[str] = Field(None, description="NFT image URL")
    blockchain: str = Field(..., description="Blockchain the NFT is on")
    contract_address: Optional[str] = Field(None, description="Smart contract address")
    token_id: Optional[str] = Field(None, description="Token ID on blockchain")
    collection_id: Optional[UUID] = Field(None, description="Collection ID")
    rarity_tier: Optional[str] = Field(None, description="Rarity tier")
    set_at: datetime = Field(..., description="When this NFT was set as PFP")
    
    class Config:
        from_attributes = True


class SetNFTPFPRequest(BaseModel):
    """Request to set an NFT as user's profile picture"""
    nft_id: UUID = Field(..., description="ID of the NFT to set as PFP")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nft_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class SetNFTPFPResponse(BaseModel):
    """Response when successfully setting NFT as PFP"""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Status message")
    pfp: NFTPFPResponse = Field(..., description="The newly set PFP")
    

class RemovePFPResponse(BaseModel):
    """Response when successfully removing PFP"""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Status message")


class UserWithPFPResponse(BaseModel):
    """User profile response including PFP information"""
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    telegram_username: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    nft_pfp_id: Optional[UUID] = Field(None, description="ID of NFT set as PFP")
    nft_pfp: Optional[NFTPFPResponse] = Field(None, description="PFP NFT details if set")
    
    class Config:
        from_attributes = True


class PublicUserProfileResponse(BaseModel):
    """Public user profile (for viewing other users)"""
    id: UUID
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    is_creator: bool
    creator_name: Optional[str]
    creator_bio: Optional[str]
    nft_pfp: Optional[NFTPFPResponse] = Field(None, description="Public PFP NFT info")
    created_at: datetime
    
    class Config:
        from_attributes = True
