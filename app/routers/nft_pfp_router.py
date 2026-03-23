"""
NFT PFP Endpoints

API routes for managing NFT profile pictures (PFP).
Allows users to set, remove, and view NFT profile pictures similar to Twitter.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db_session
from app.models import User, NFT
from app.utils.auth import get_current_user
from app.schemas.nft_pfp import (
    SetNFTPFPRequest,
    SetNFTPFPResponse,
    RemovePFPResponse,
    NFTPFPResponse,
    UserWithPFPResponse,
    PublicUserProfileResponse,
)
from app.services.nft_pfp_service import NFTPFPService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pfp", tags=["nft-pfp"])


@router.post("/set/{nft_id}", response_model=SetNFTPFPResponse, status_code=status.HTTP_200_OK)
async def set_nft_as_pfp(
    nft_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> SetNFTPFPResponse:
    """
    Set an NFT owned by the user as their profile picture.
    
    The NFT must:
    - Belong to the authenticated user
    - Not be currently locked
    - Be a valid NFT in the system
    
    Returns the newly set PFP information.
    
    ✅ Status Codes:
    - 200: Successfully set NFT as PFP
    - 400: NFT not found, locked, or doesn't belong to user
    - 401: Unauthorized - not authenticated
    - 404: NFT does not exist
    """
    nft, error = await NFTPFPService.set_nft_as_pfp(
        db=db,
        user_id=current_user.id,
        nft_id=nft_id,
    )
    
    if error:
        logger.warning(f"Failed to set PFP for user {current_user.id}: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    pfp_response = NFTPFPResponse.model_validate(nft)
    logger.info(f"✓ User {current_user.id} set NFT {nft_id} as PFP")
    
    return SetNFTPFPResponse(
        success=True,
        message=f"Successfully set '{nft.name}' as your profile picture",
        pfp=pfp_response,
    )


@router.delete("/remove", response_model=RemovePFPResponse, status_code=status.HTTP_200_OK)
async def remove_nft_pfp(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> RemovePFPResponse:
    """
    Remove the current NFT profile picture.
    
    After removal, the user will use their regular avatar_url instead.
    
    ✅ Status Codes:
    - 200: Successfully removed PFP
    - 400: No PFP is currently set
    - 401: Unauthorized - not authenticated
    """
    success, error = await NFTPFPService.remove_nft_pfp(
        db=db,
        user_id=current_user.id,
    )
    
    if not success:
        logger.warning(f"Failed to remove PFP for user {current_user.id}: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    logger.info(f"✓ Removed PFP for user {current_user.id}")
    
    return RemovePFPResponse(
        success=True,
        message="Successfully removed your NFT profile picture",
    )


@router.get("/me", response_model=NFTPFPResponse, status_code=status.HTTP_200_OK)
async def get_my_pfp(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> NFTPFPResponse:
    """
    Get the current user's NFT profile picture.
    
    Returns the details of the NFT currently set as the user's PFP.
    
    ✅ Status Codes:
    - 200: PFP found and returned
    - 404: No PFP is currently set
    - 401: Unauthorized - not authenticated
    """
    pfp = await NFTPFPService.get_user_pfp(
        db=db,
        user_id=current_user.id,
    )
    
    if not pfp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No NFT profile picture is currently set",
        )
    
    return pfp


@router.get("/user/{user_id}", response_model=NFTPFPResponse, status_code=status.HTTP_200_OK)
async def get_user_pfp(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> NFTPFPResponse:
    """
    Get another user's NFT profile picture (public endpoint).
    
    Returns the details of the NFT set as the requested user's PFP.
    This is a public endpoint - anyone can view other users' PFPs.
    
    ✅ Status Codes:
    - 200: PFP found and returned
    - 404: User not found or no PFP is set
    """
    pfp = await NFTPFPService.get_user_pfp(
        db=db,
        user_id=user_id,
    )
    
    if not pfp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or has no NFT profile picture set",
        )
    
    return pfp


@router.get("/me/profile", response_model=UserWithPFPResponse, status_code=status.HTTP_200_OK)
async def get_my_profile_with_pfp(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserWithPFPResponse:
    """
    Get the current user's profile with their NFT PFP details.
    
    Returns the user profile including the NFT PFP information if set.
    
    ✅ Status Codes:
    - 200: Profile returned
    - 401: Unauthorized - not authenticated
    """
    user = await NFTPFPService.get_user_with_pfp(
        db=db,
        user_id=current_user.id,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Build response with PFP
    pfp_response = None
    if user.nft_pfp_id and user.nft_pfp_rel:
        pfp_response = NFTPFPResponse.model_validate(user.nft_pfp_rel)
    
    response = UserWithPFPResponse.model_validate(user)
    if pfp_response:
        response.nft_pfp = pfp_response
    
    return response
