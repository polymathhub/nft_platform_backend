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
from app.services.auth_service import AuthService
from app.models.wallet import BlockchainType
from app.models import User
from app.utils.security import verify_token
from app.utils.auth import get_current_user
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wallets", tags=["wallets"])
async def get_current_user_id_from_header(authorization: str = None) -> UUID:
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("[Wallet Auth] Missing or invalid authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        logger.warning("[Wallet Auth] Empty token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty token",
        )
    try:
        user_id = AuthService.verify_token(token)
        if not user_id:
            logger.warning("[Wallet Auth] Token verification returned None")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        try:
            return UUID(str(user_id))
        except (ValueError, TypeError) as e:
            logger.error(f"[Wallet Auth] Invalid user_id format: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Wallet Auth] Token verification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
        )
@router.post("/create", response_model=dict)
async def create_wallet(
    request: CreateWalletRequest,
    user_id: str | None = None,
    db: AsyncSession = Depends(get_db_session),
    authorization: str | None = None,
) -> dict:
    try:
        from app.models import User
        from app.models.wallet import WalletType
        from app.utils.wallet_address_generator import WalletAddressGenerator
        from sqlalchemy import select
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id query parameter is required",
            )
        try:
            uid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user_id format",
            )
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        try:
            blockchain_type = BlockchainType[request.blockchain.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid blockchain: {request.blockchain}. Valid values: {[b.name for b in BlockchainType]}",
            )
        try:
            wallet_type = WalletType[request.wallet_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid wallet_type: {request.wallet_type}. Valid values: {[w.name for w in WalletType]}",
            )
        address = WalletAddressGenerator.generate_address(blockchain_type)
        wallet, error = await WalletService.create_wallet(
            db=db,
            user_id=uid,
            blockchain=blockchain_type,
            wallet_type=wallet_type,
            address=address,
            is_primary=request.is_primary,
        )
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create wallet: {error}",
            )
        logger.info(f"Wallet created: {wallet.id} for user {uid} on {blockchain_type.value}")
        return {
            "success": True,
            "wallet": {
                "id": str(wallet.id),
                "blockchain": wallet.blockchain.value,
                "address": wallet.address,
                "wallet_type": wallet.wallet_type.value,
                "is_primary": wallet.is_primary,
                "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create wallet error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create wallet: {str(e)}",
        )
@router.post("/import", response_model=dict)
async def import_wallet(
    request: ImportWalletRequest,
    user_id: str | None = None,
    db: AsyncSession = Depends(get_db_session),
    authorization: str | None = None,
) -> dict:
    try:
        from app.models import User
        from app.models.wallet import WalletType
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id query parameter is required",
            )
        try:
            uid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user_id format",
            )
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        try:
            blockchain_type = BlockchainType[request.blockchain.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid blockchain: {request.blockchain}",
            )
        try:
            wallet_type = WalletType[request.wallet_type.upper()]
        except KeyError:
            wallet_type = WalletType.SELF_CUSTODY
        wallet, error = await WalletService.import_wallet(
            db=db,
            user_id=uid,
            blockchain=blockchain_type,
            address=request.address,
            is_primary=request.is_primary,
            public_key=request.public_key,
        )
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to import wallet: {error}",
            )
        logger.info(f"Wallet imported: {wallet.id} for user {uid} on {blockchain_type.value}")
        return {
            "success": True,
            "wallet": {
                "id": str(wallet.id),
                "blockchain": wallet.blockchain.value,
                "address": wallet.address,
                "wallet_type": wallet.wallet_type.value,
                "is_primary": wallet.is_primary,
                "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
            },
        }
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
    try:
        if not user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")
        from uuid import UUID as _UUID
        try:
            uid = _UUID(user_id)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid user_id format: {user_id} - {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_id format. Must be a valid UUID (e.g., 550e8400-e29b-41d4-a716-446655440000)"
            )
        bc = None
        if blockchain:
            try:
                bc = BlockchainType(blockchain)
            except Exception:
                bc = None
        wallets = await WalletService.get_user_wallets(db, uid, bc)
        result = []
        for w in wallets:
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
        logger.error(f"List wallets error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
@router.post("/generate")
async def generate_wallets(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
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
    try:
        from app.models import User
        uid = UUID(user_id)
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
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
    try:
        from app.models import User, Wallet
        uid = UUID(user_id)
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
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
    try:
        from app.models import User
        uid = UUID(user_id)
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
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
