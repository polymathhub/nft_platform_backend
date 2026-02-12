from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db_session
from app.utils.auth import get_current_user
from app.services.attestation_service import AttestationService
from app.schemas.attestation import (
    CreateAttestationRequest,
    AttestationResponse,
    NFTAttestationsResponse,
    VerifiedAttestationResponse,
    AttesterHistoryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/attestations", tags=["attestations"])


@router.post("", response_model=AttestationResponse, status_code=status.HTTP_201_CREATED)
async def create_attestation(
    request: CreateAttestationRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> AttestationResponse:
    """Create a new attestation for an NFT."""
    attestation, error = await AttestationService.create_attestation(
        db=db,
        nft_id=request.nft_id,
        attester_address=current_user.wallet_address,
        attestation_type=request.attestation_type,
        score=request.score,
        metadata=request.metadata,
        signature=request.signature,
        duration_days=request.duration_days,
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return AttestationResponse.model_validate(attestation)


@router.get("/nft/{nft_id}", response_model=NFTAttestationsResponse)
async def get_nft_attestations(
    nft_id: UUID,
    status: str | None = None,
    attestation_type: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
) -> NFTAttestationsResponse:
    """Get attestations for an NFT."""
    attestations, total = await AttestationService.get_nft_attestations(
        db=db,
        nft_id=nft_id,
        status=status,
        attestation_type=attestation_type,
        skip=skip,
        limit=limit,
    )
    return NFTAttestationsResponse(
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        items=[AttestationResponse.model_validate(a) for a in attestations],
    )


@router.get("/nft/{nft_id}/verified", response_model=VerifiedAttestationResponse)
async def get_verified_attestations(
    nft_id: UUID,
    attestation_type: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> VerifiedAttestationResponse:
    """Get verified attestations for an NFT."""
    attestations = await AttestationService.get_verified_attestations(
        db=db, nft_id=nft_id, attestation_type=attestation_type
    )

    average_score = (
        sum(a.score for a in attestations) / len(attestations)
        if attestations
        else 0.0
    )

    return VerifiedAttestationResponse(
        items=[AttestationResponse.model_validate(a) for a in attestations],
        verified_count=len(attestations),
        average_score=average_score,
    )


@router.post("/{attestation_id}/verify", response_model=AttestationResponse)
async def verify_attestation(
    attestation_id: UUID,
    transaction_hash: str | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> AttestationResponse:
    """Verify an attestation."""
    attestation, error = await AttestationService.verify_attestation(
        db=db, attestation_id=attestation_id, transaction_hash=transaction_hash
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return AttestationResponse.model_validate(attestation)


@router.post("/{attestation_id}/reject", response_model=AttestationResponse)
async def reject_attestation(
    attestation_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> AttestationResponse:
    """Reject an attestation."""
    attestation, error = await AttestationService.reject_attestation(
        db=db, attestation_id=attestation_id
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return AttestationResponse.model_validate(attestation)


@router.get("/{attestation_id}", response_model=AttestationResponse)
async def get_attestation(
    attestation_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> AttestationResponse:
    """Get attestation by ID."""
    attestation = await AttestationService.get_attestation_by_id(
        db=db, attestation_id=attestation_id
    )
    if not attestation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attestation not found")

    return AttestationResponse.model_validate(attestation)


@router.get("/attester/{attester_address}", response_model=AttesterHistoryResponse)
async def get_attester_history(
    attester_address: str,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
) -> AttesterHistoryResponse:
    """Get attestation history for an attester."""
    attestations, total = await AttestationService.get_attester_history(
        db=db, attester_address=attester_address, skip=skip, limit=limit
    )
    return AttesterHistoryResponse(
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        attester_address=attester_address,
        items=[AttestationResponse.model_validate(a) for a in attestations],
    )
