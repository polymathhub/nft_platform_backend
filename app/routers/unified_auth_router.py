from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging
from app.database import get_db_session
from app.models import User
from app.schemas.auth_unified import (
    TelegramAuthRequest,
    TONWalletAuthRequest,
    AuthSuccessResponse,
    AuthErrorResponse,
    AuthMethodEnum,
    TokenResponse,
    UserIdentityResponse,
    IdentityData,
    InitDataSource,
)
from app.services.unified_user_service import UnifiedUserService
from app.services.unified_token_service import UnifiedTokenService
from app.services.security_service import UnifiedSecurityService
from app.utils.auth import get_current_user
from app.config import get_settings
router = APIRouter(prefix="/api/v1/auth", tags=["unified-auth"])
logger = logging.getLogger(__name__)
settings = get_settings()
@router.post("/telegram/login", response_model=AuthSuccessResponse)
async def telegram_login(
    request: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db_session),
):
    try:
        logger.warning(f"[Telegram Login] 1️⃣ Starting authentication")
        
        is_valid, error = UnifiedSecurityService.verify_telegram_initdata(
            request.init_data,
            settings.telegram_bot_token
        )
        if not is_valid:
            logger.error(f"[Telegram Login] ✗ Telegram signature verification FAILED: {error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error or "Invalid Telegram signature"
            )
        
        logger.warning(f"[Telegram Login] 2️⃣ Telegram signature verified")
        
        identity = UnifiedSecurityService.extract_telegram_identity(request.init_data)
        if not identity:
            logger.error(f"[Telegram Login] ✗ Failed to extract Telegram identity")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to extract Telegram identity"
            )
        
        logger.warning(f"[Telegram Login] 3️⃣ Identity extracted: telegram_id={identity.telegram_id}, username='{identity.telegram_username}' (set={bool(identity.telegram_username)})")
        
        user, error = await UnifiedUserService.get_or_create_user_from_identity(
            db=db,
            identity=identity,
        )
        if error or not user:
            logger.error(f"[Telegram Login] ✗ Failed to create/get user: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Failed to create user"
            )
        
        logger.warning(f"[Telegram Login] 4️⃣ User initialized: id={user.id}, username='{user.username}', email={user.email}, full_name='{user.full_name}'")
        
        tokens = UnifiedTokenService.generate_tokens(str(user.id))
        logger.warning(f"[Telegram Login] 5️⃣ Tokens generated for user {user.id}")
        
        response = AuthSuccessResponse(
            success=True,
            auth_method=AuthMethodEnum.TELEGRAM,
            user=UserIdentityResponse.model_validate(user),
            tokens=TokenResponse(**tokens),
        )
        
        logger.warning(f"[Telegram Login] ✅ SUCCESS: user_id={user.id}, username='{user.username}', email={user.email}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Telegram Login] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )
@router.post("/ton/login", response_model=AuthSuccessResponse)
async def ton_login(
    request: TONWalletAuthRequest,
    db: AsyncSession = Depends(get_db_session),
):
    try:
        if not request.wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wallet address required"
            )
        is_valid, error = UnifiedSecurityService.verify_ton_wallet_address(
            request.wallet_address
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Invalid TON wallet address format"
            )
        identity = UnifiedSecurityService.extract_ton_identity(
            request.wallet_address,
            request.wallet_metadata
        )
        if not identity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to extract TON identity"
            )
        user, error = await UnifiedUserService.get_or_create_user_from_identity(
            db=db,
            identity=identity,
        )
        if error or not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Failed to create user"
            )
        tokens = UnifiedTokenService.generate_tokens(str(user.id))
        logger.info(f"User {user.id} authenticated via TON wallet {request.wallet_address}")
        return AuthSuccessResponse(
            success=True,
            auth_method=AuthMethodEnum.TON_WALLET,
            user=UserIdentityResponse.model_validate(user),
            tokens=TokenResponse(**tokens),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TON auth error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )
@router.post("/link-wallet")
async def link_wallet(
    request: TONWalletAuthRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        if not request.wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wallet address required"
            )
        wallet, error = await UnifiedUserService.link_ton_wallet_to_user(
            db=db,
            user_id=str(current_user.id),
            wallet_address=request.wallet_address,
            wallet_metadata=request.wallet_metadata,
        )
        if error or not wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Failed to link wallet"
            )
        logger.info(f"TON wallet linked to user {current_user.id}")
        return {
            "success": True,
            "message": "Wallet linked successfully",
            "wallet_address": request.wallet_address,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Link wallet error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link wallet"
        )
@router.get("/profile", response_model=UserIdentityResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    logger.info(f"[Auth Profile] Returning user profile: user_id={current_user.id}, username={current_user.username}, email={current_user.email}")
    return UserIdentityResponse.model_validate(current_user)
@router.post("/logout")
async def logout():
    return {"success": True, "message": "Logged out successfully"}
