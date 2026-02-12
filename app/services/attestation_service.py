import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.models import NFT
from app.models.attestation import Attestation, AttestationType, AttestationStatus
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AttestationService:

    @staticmethod
    async def create_attestation(
        db: AsyncSession,
        nft_id: UUID,
        attester_address: str,
        attestation_type: str,
        score: float = 0.0,
        metadata: Optional[dict] = None,
        signature: Optional[str] = None,
        duration_days: Optional[int] = 365,
    ) -> tuple[Optional[Attestation], Optional[str]]:
        result = await db.execute(select(NFT).where(NFT.id == nft_id))
        nft = result.scalar_one_or_none()
        if not nft:
            return None, "NFT not found"

        if score < 0.0 or score > 1.0:
            return None, "Score must be between 0.0 and 1.0"

        attestation = Attestation(
            nft_id=nft_id,
            attester_address=attester_address,
            attestation_type=attestation_type,
            status=AttestationStatus.PENDING,
            score=score,
            attestation_metadata=metadata or {},
            signature=signature,
        )

        if duration_days:
            attestation.expires_at = datetime.utcnow() + timedelta(days=duration_days)

        db.add(attestation)
        await db.commit()
        await db.refresh(attestation)
        return attestation, None

    @staticmethod
    async def verify_attestation(
        db: AsyncSession,
        attestation_id: UUID,
        transaction_hash: Optional[str] = None,
    ) -> tuple[Optional[Attestation], Optional[str]]:

        result = await db.execute(
            select(Attestation).where(Attestation.id == attestation_id)
        )
        attestation = result.scalar_one_or_none()
        if not attestation:
            return None, "Attestation not found"

        attestation.status = AttestationStatus.VERIFIED
        attestation.verified_at = datetime.utcnow()
        attestation.transaction_hash = transaction_hash
        await db.commit()
        await db.refresh(attestation)
        return attestation, None

    @staticmethod
    async def reject_attestation(
        db: AsyncSession,
        attestation_id: UUID,
    ) -> tuple[Optional[Attestation], Optional[str]]:

        result = await db.execute(
            select(Attestation).where(Attestation.id == attestation_id)
        )
        attestation = result.scalar_one_or_none()
        if not attestation:
            return None, "Attestation not found"

        if attestation.status != AttestationStatus.PENDING:
            return None, f"Cannot reject attestation with status {attestation.status}"

        attestation.status = AttestationStatus.REJECTED
        await db.commit()
        await db.refresh(attestation)
        return attestation, None

    @staticmethod
    async def get_nft_attestations(
        db: AsyncSession,
        nft_id: UUID,
        status: Optional[str] = None,
        attestation_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[Attestation], int]:

        query = select(Attestation).where(Attestation.nft_id == nft_id)

        if status:
            query = query.where(Attestation.status == status)
        if attestation_type:
            query = query.where(Attestation.attestation_type == attestation_type)

        count_result = await db.execute(select(Attestation).where(Attestation.nft_id == nft_id))
        total = len(count_result.scalars().all())

        result = await db.execute(
            query.order_by(desc(Attestation.created_at)).offset(skip).limit(limit)
        )
        attestations = result.scalars().all()
        return attestations, total

    @staticmethod
    async def get_verified_attestations(
        db: AsyncSession,
        nft_id: UUID,
        attestation_type: Optional[str] = None,
    ) -> List[Attestation]:
        """
        Get verified attestations for an NFT.

        Args:
            db: Database session
            nft_id: NFT ID
            attestation_type: Filter by type

        Returns:
            List of verified attestations
        """
        query = select(Attestation).where(
            and_(
                Attestation.nft_id == nft_id,
                Attestation.status == AttestationStatus.VERIFIED,
            )
        )

        if attestation_type:
            query = query.where(Attestation.attestation_type == attestation_type)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_attester_history(
        db: AsyncSession,
        attester_address: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[Attestation], int]:
        """
        Get attestation history for an attester.

        Args:
            db: Database session
            attester_address: Attester address
            skip: Skip count
            limit: Limit count

        Returns:
            Tuple of (attestations, total_count)
        """
        query = select(Attestation).where(Attestation.attester_address == attester_address)

        count_result = await db.execute(query)
        total = len(count_result.scalars().all())

        result = await db.execute(
            query.order_by(desc(Attestation.created_at)).offset(skip).limit(limit)
        )
        attestations = result.scalars().all()
        return attestations, total

    @staticmethod
    async def get_attestation_by_id(
        db: AsyncSession,
        attestation_id: UUID,
    ) -> Optional[Attestation]:
        """Get attestation by ID."""
        result = await db.execute(
            select(Attestation).where(Attestation.id == attestation_id)
        )
        return result.scalar_one_or_none()
