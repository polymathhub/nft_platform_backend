from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request
from sqlalchemy import select
from app.utils.auth import get_current_user
from app.models import Wallet
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db_session
from app.schemas.nft import (
    MintNFTRequest,
    TransferNFTRequest,
    LockNFTRequest,
    UnlockNFTRequest,
    NFTResponse,
    NFTDetailResponse,
    UserNFTListResponse,
    NFTMetadataUploadResponse,
)
from app.services.nft_service import NFTService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/nfts", tags=["nfts"])


@router.post("/mint", response_model=NFTDetailResponse)
async def mint_nft(
    request: MintNFTRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> NFTDetailResponse:
    """
    Complete NFT minting flow:
    1. Create NFT record in database
    2. Mint on blockchain
    3. Confirm transaction and update record
    """
    nft, error = await NFTService.mint_nft_with_blockchain_confirmation(
        db=db,
        user_id=current_user.id,
        wallet_id=request.wallet_id,
        name=request.name,
        description=request.description,
        image_url=request.image_url,
        royalty_percentage=request.royalty_percentage,
        metadata=request.metadata,
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return NFTDetailResponse.model_validate(nft)


@router.post("/{nft_id}/transfer", response_model=NFTDetailResponse)
async def transfer_nft(
    nft_id: UUID,
    request: TransferNFTRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> NFTDetailResponse:
    nft = await NFTService.get_nft_by_id(db, nft_id)
    if not nft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NFT not found")

    if str(nft.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="unauthorized")

    transferred, error = await NFTService.transfer_nft(
        db=db,
        nft_id=nft_id,
        to_address=request.to_address,
        transaction_hash=request.transaction_hash or "",
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return NFTDetailResponse.model_validate(transferred)


@router.post("/{nft_id}/burn", response_model=NFTDetailResponse, status_code=status.HTTP_202_ACCEPTED)
async def burn_nft(
    nft_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> NFTDetailResponse:
    nft = await NFTService.get_nft_by_id(db, nft_id)
    if not nft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NFT not found")
    if str(nft.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="unauthorized")

    burned, error = await NFTService.burn_nft(db=db, nft_id=nft_id, transaction_hash="")
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return NFTDetailResponse.model_validate(burned)


@router.post("/{nft_id}/lock", response_model=NFTDetailResponse)
async def lock_nft(
    nft_id: UUID,
    request: LockNFTRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> NFTDetailResponse:
    """Lock an NFT to prevent transfers."""
    nft = await NFTService.get_nft_by_id(db, nft_id)
    if not nft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NFT not found")
    if str(nft.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="unauthorized")

    locked, error = await NFTService.lock_nft(
        db=db,
        nft_id=nft_id,
        reason=request.reason,
        duration_hours=request.duration_hours,
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return NFTDetailResponse.model_validate(locked)


@router.post("/{nft_id}/unlock", response_model=NFTDetailResponse)
async def unlock_nft(
    nft_id: UUID,
    request: UnlockNFTRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> NFTDetailResponse:
    """Unlock an NFT to allow transfers."""
    nft = await NFTService.get_nft_by_id(db, nft_id)
    if not nft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NFT not found")
    if str(nft.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="unauthorized")

    unlocked, error = await NFTService.unlock_nft(db=db, nft_id=nft_id)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return NFTDetailResponse.model_validate(unlocked)


@router.get("/user/collection", response_model=UserNFTListResponse)
async def get_user_nfts(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    blockchain: str | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> UserNFTListResponse:
    nfts, total = await NFTService.get_user_nfts(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status,
        blockchain=blockchain,
    )
    items = [NFTResponse.model_validate(n) for n in nfts]
    return UserNFTListResponse(total=total, page=(skip // limit) + 1, per_page=limit, items=items)


@router.get("/{nft_id}", response_model=NFTDetailResponse)
async def get_nft(
    nft_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> NFTDetailResponse:
    nft = await NFTService.get_nft_by_id(db, nft_id)
    if not nft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NFT not found",
        )
    return NFTDetailResponse.model_validate(nft)


@router.post("/metadata/upload", response_model=NFTMetadataUploadResponse)
async def upload_nft_metadata(
    metadata: dict,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> NFTMetadataUploadResponse:
    if not metadata.get("name"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing name")

    uploaded = await NFTService.upload_metadata_to_ipfs(metadata)
    if not uploaded:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="ipfs upload failed")
    ipfs_hash, gateway = uploaded
    return NFTMetadataUploadResponse(ipfs_hash=ipfs_hash, ipfs_url=f"ipfs://{ipfs_hash}", gateway_url=gateway)
