from __future__ import annotations

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
    """
    Extract user ID from authorization header.
    
    Note: Full token verification should be implemented.
    Currently accepts user_id via header for development.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    token = authorization.replace("Bearer ", "")
    try:
        # TODO: Implement proper JWT token verification
        # For now, accept token as user_id for development
        return UUID(token)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Invalid token format: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
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
        from app.models.wallet import WalletType
        from app.utils.wallet_address_generator import WalletAddressGenerator
        from sqlalchemy import select
        
        # Verify user exists
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Convert blockchain string to BlockchainType enum
        try:
            blockchain_type = BlockchainType[blockchain.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid blockchain: {blockchain}",
            )
        
        # Generate address for the blockchain
        address = WalletAddressGenerator.generate_address(blockchain_type)
        
        # Create wallet
        wallet, error = await WalletService.create_wallet(
            db=db,
            user_id=UUID(user_id),
            blockchain=blockchain_type,
            wallet_type=WalletType.CUSTODIAL,
            address=address,
            is_primary=False,
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
                "blockchain": wallet.blockchain.value,
                "address": wallet.address,
                "wallet_type": wallet.wallet_type.value,
                "is_primary": wallet.is_primary,
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
    user_id: str,
    request: ImportWalletRequest,
    db: AsyncSession = Depends(get_db_session),
) -> WalletResponse:
    """
    Import an existing wallet for a user.
    
    Args:
        user_id: User UUID as string
        request: Wallet import request with blockchain, address, and optional private key
    """
    try:
        from app.models import User
        
        uid = UUID(user_id)
        
        # Verify user exists
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Import wallet
        wallet, error = await WalletService.import_wallet(
            db=db,
            user_id=uid,
            blockchain=request.blockchain,
            address=request.address,
            private_key=request.private_key,
            name=request.name or f"Imported {request.blockchain.capitalize()} Wallet"
        )
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to import wallet: {error}",
            )
        
        return WalletResponse.model_validate({
            "id": wallet.id,
            "blockchain": wallet.blockchain.value,
            "address": wallet.address,
            "is_primary": wallet.is_primary,
            "is_active": wallet.is_active,
            "created_at": wallet.created_at,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import wallet error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import wallet: {str(e)}",
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
    user_id: str,
    request: SetPrimaryWalletRequest,
    db: AsyncSession = Depends(get_db_session),
) -> WalletResponse:
    """
    Set a wallet as the primary wallet for a user.
    
    Args:
        user_id: User UUID as string
        request: Request containing wallet_id to set as primary
    """
    try:
        from app.models import User
        
        uid = UUID(user_id)
        
        # Verify user exists
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Set primary wallet
        wallet, error = await WalletService.set_primary_wallet(
            db=db,
            wallet_id=request.wallet_id,
            user_id=uid,
        )
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to set primary wallet: {error}",
            )
        
        return WalletResponse.model_validate({
            "id": wallet.id,
            "blockchain": wallet.blockchain.value,
            "address": wallet.address,
            "is_primary": wallet.is_primary,
            "is_active": wallet.is_active,
            "created_at": wallet.created_at,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set primary wallet error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set primary wallet: {str(e)}",
        )


@router.get("/user/{user_id}/balance")
async def get_user_balance(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get total USDT balance across all user's wallets.
    Returns balance per blockchain and total balance.
    """
    try:
        from app.models import User, Wallet
        
        uid = UUID(user_id)
        
        # Verify user exists
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Get all user wallets
        wallets_result = await db.execute(
            select(Wallet).where(Wallet.user_id == uid)
        )
        wallets = wallets_result.scalars().all()
        
        balance_data = {
            "user_id": str(uid),
            "username": user.username,
            "total_balance_usd": 0.0,
            "wallets": [],
        }
        
        for wallet in wallets:
            wallet_info = {
                "wallet_id": str(wallet.id),
                "address": wallet.address[:10] + "..." + wallet.address[-10:],
                "blockchain": wallet.blockchain.value,
                "is_primary": wallet.is_primary,
                "balance": wallet.wallet_metadata.get("balance", 0.0) if wallet.wallet_metadata else 0.0,
            }
            balance_data["wallets"].append(wallet_info)
            balance_data["total_balance_usd"] += wallet_info["balance"]
        
        return balance_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user balance error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get balance: {str(e)}",
        )


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_wallet(
    wallet_id: UUID,
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Deactivate a wallet for a user.
    
    Args:
        wallet_id: Wallet UUID
        user_id: User UUID as string
    """
    try:
        from app.models import User
        
        uid = UUID(user_id)
        
        # Verify user exists
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Deactivate wallet
        success, error = await WalletService.deactivate_wallet(
            db=db,
            wallet_id=wallet_id,
            user_id=uid,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to deactivate wallet: {error}",
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate wallet error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate wallet: {str(e)}",
        )
