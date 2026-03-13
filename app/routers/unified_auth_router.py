"""Unified authentication endpoints for TON Wallet and Telegram.

Provides consistent, standardized handlers for both authentication methods.
"""

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
    """
    Authenticate user via Telegram WebApp.
    
    Validates Telegram init_data, creates/updates user, and returns JWT tokens.
    """
    try:
        # Validate Telegram data signature and extract identity
        is_valid, error = UnifiedSecurityService.verify_telegram_initdata(
            request.init_data,
            settings.telegram_bot_token
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error or "Invalid Telegram signature"
            )
        
        # Extract identity from validated initData
        identity = UnifiedSecurityService.extract_telegram_identity(request.init_data)
        if not identity:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to extract Telegram identity"
            )

        # Create or get user
        user, error = await UnifiedUserService.get_or_create_user_from_identity(
            db=db,
            identity=identity,
        )
        
        if error or not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Failed to create user"
            )

        # Generate tokens
        tokens = UnifiedTokenService.generate_tokens(str(user.id))

        logger.info(f"User {user.id} authenticated via Telegram")

        return AuthSuccessResponse(
            success=True,
            auth_method=AuthMethodEnum.TELEGRAM,
            user=UserIdentityResponse.model_validate(user),
            tokens=TokenResponse(**tokens),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telegram auth error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/ton/login", response_model=AuthSuccessResponse)
async def ton_login(
    request: TONWalletAuthRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Authenticate user via TON Wallet (TonConnect).
    
    Validates wallet address, creates/updates user, and returns JWT tokens.
    """
    try:
        if not request.wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wallet address required"
            )

        # Validate TON wallet address format and extract identity
        is_valid, error = UnifiedSecurityService.verify_ton_wallet_address(
            request.wallet_address
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Invalid TON wallet address format"
            )
        
        # Extract identity from wallet address
        identity = UnifiedSecurityService.extract_ton_identity(
            request.wallet_address,
            request.wallet_metadata
        )
        
        if not identity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to extract TON identity"
            )

        # Create or get user
        user, error = await UnifiedUserService.get_or_create_user_from_identity(
            db=db,
            identity=identity,
        )
        
        if error or not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Failed to create user"
            )

        # Generate tokens
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
    """
    Link a TON wallet to an existing user account.
    
    Allows users authenticated via one method to add another auth method.
    """
    try:
        if not request.wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wallet address required"
            )

        # Link wallet to user
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


@router.get("/profile", response_model=dict)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    """Get authenticated user's profile."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "telegram_id": current_user.telegram_id,
        "ton_wallet_address": getattr(current_user, 'ton_wallet_address', None),
        "avatar": current_user.avatar_url,
        "role": current_user.user_role,
        "created_at": current_user.created_at,
    }


@router.post("/logout")
async def logout():
    """Logout endpoint. Token invalidation handled by client."""
    return {"success": True, "message": "Logged out successfully"}
