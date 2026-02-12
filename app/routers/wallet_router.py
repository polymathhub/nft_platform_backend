import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db_session
from app.schemas.wallet import (
    CreateWalletRequest,
    ImportWalletRequest,
    WalletResponse,
    WalletDetailResponse,
    SetPrimaryWalletRequest,
)
from app.services.wallet_service import WalletService
from app.models.wallet import BlockchainType
from app.utils.security import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wallets", tags=["wallets"])


async def get_current_user_id(authorization: str = None) -> UUID:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing auth",
        )
    token = authorization.replace("Bearer ", "")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token verification not implemented in router",
    )


@router.post("/create", response_model=WalletResponse)
async def create_wallet(
    user_id: str,
    blockchain: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Create a new wallet for a user."""
    try:
        from app.models import User
        from sqlalchemy import select
        
        # Verify user exists
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Create wallet
        wallet, error = await WalletService.create_wallet(
            db=db,
            user_id=UUID(user_id),
            blockchain=blockchain,
            name=f"{blockchain.capitalize()} Wallet"
        )
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create wallet: {error}",
            )
        
        return {
            "success": True,
            "wallet": {
                "id": str(wallet.id),
                "name": wallet.name,
                "blockchain": wallet.blockchain.value,
                "address": wallet.address,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create wallet error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create wallet: {str(e)}",
        )


@router.post("/import", response_model=WalletResponse)
async def import_wallet(
    request: ImportWalletRequest,
    db: AsyncSession = Depends(get_db_session),
    authorization: str = None,
) -> WalletResponse:
    # Authentication is TODO; accept explicit user_id in header or query for now
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Import endpoint is not implemented in this environment",
    )


@router.get("", response_model=list[WalletResponse])
async def list_user_wallets(
    user_id: str | None = None,
    blockchain: str | None = None,
    db: AsyncSession = Depends(get_db_session),
    authorization: str = None,
) -> list[WalletResponse]:
    """List wallets for a user. Provide `user_id` as UUID string."""
    try:
        if not user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")
        from uuid import UUID as _UUID

        uid = _UUID(user_id)
        bc = None
        if blockchain:
            try:
                bc = BlockchainType(blockchain)
            except Exception:
                bc = None

        wallets = await WalletService.get_user_wallets(db, uid, bc)
        result = []
        for w in wallets:
            # Map model fields to response schema fields
            item = {
                "id": w.id,
                "blockchain": w.blockchain.value if w.blockchain else None,
                "wallet_type": w.wallet_type.value if w.wallet_type else None,
                "address": w.address,
                "public_key": w.public_key,
                "is_primary": w.is_primary,
                "is_active": w.is_active,
                "metadata": getattr(w, "wallet_metadata", None),
                "created_at": w.created_at,
                "updated_at": w.updated_at,
            }
            result.append(WalletResponse.model_validate(item))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List wallets error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate")
async def generate_wallets(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Generate a bundle of wallets for the user. Returns public addresses only."""
    try:
        from uuid import UUID as _UUID
        uid = _UUID(user_id)

        addresses = await WalletService.generate_wallet_bundle(db, uid, make_primary=True)
        return {"success": True, "addresses": addresses}
    except Exception as e:
        logger.error(f"Generate wallets error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{wallet_id}", response_model=WalletDetailResponse)
async def get_wallet_details(
    wallet_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    authorization: str = None,
) -> WalletDetailResponse:
    wallet = await WalletService.get_wallet_by_id(db, wallet_id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found",
        )
    return WalletDetailResponse.model_validate(wallet)


@router.post("/set-primary", response_model=WalletResponse)
async def set_primary_wallet(
    request: SetPrimaryWalletRequest,
    db: AsyncSession = Depends(get_db_session),
    authorization: str = None,
) -> WalletResponse:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Endpoint requires proper authentication setup",
    )


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_wallet(
    wallet_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    authorization: str = None,
):
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Endpoint requires proper authentication setup",
    )
