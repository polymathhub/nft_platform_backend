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
    UnifiedAuthRequest,
    UnifiedAuthResponse,
    AuthMethodType,
)
from app.services.unified_user_service import UnifiedUserService
from app.services.unified_token_service import UnifiedTokenService
from app.utils.auth import get_current_user
from app.utils.telegram_security import verify_telegram_data
from app.config import get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["unified-auth"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/telegram/login", response_model=UnifiedAuthResponse)
async def telegram_login(
    request: UnifiedAuthRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Authenticate user via Telegram WebApp.
    
    Validates Telegram init_data, creates/updates user, and returns JWT tokens.
    """
    try:
        # Validate Telegram data signature
        if not verify_telegram_data(request.init_data):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Telegram signature"
            )

        # Extract user info from init_data
        telegram_user = request.telegram_data.get("user", {})
        telegram_id = str(telegram_user.get("id"))
        telegram_username = telegram_user.get("username")

        if not telegram_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Telegram user data"
            )

        # Create or get user
        user = await UnifiedUserService.get_or_create_user_by_telegram(
            db=db,
            telegram_id=telegram_id,
            telegram_username=telegram_username,
        )

        # Generate tokens
        tokens = UnifiedTokenService.generate_tokens(user.id)

        logger.info(f"User {user.id} authenticated via Telegram")

        return UnifiedAuthResponse(
            user=user,
            tokens=tokens,
            auth_method=AuthMethodType.TELEGRAM,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telegram auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/ton/login", response_model=UnifiedAuthResponse)
async def ton_login(
    request: UnifiedAuthRequest,
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

        # Normalize wallet address
        wallet_address = request.wallet_address.lower().strip()

        # Validate TON wallet format (basic check)
        if not wallet_address.startswith("0:") and not wallet_address.startswith("u"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TON wallet address format"
            )

        # Create or get user
        user = await UnifiedUserService.get_or_create_user_by_ton_wallet(
            db=db,
            wallet_address=wallet_address,
            wallet_metadata=request.ton_wallet_metadata,
        )

        # Generate tokens
        tokens = UnifiedTokenService.generate_tokens(user.id)

        logger.info(f"User {user.id} authenticated via TON wallet {wallet_address}")

        return UnifiedAuthResponse(
            user=user,
            tokens=tokens,
            auth_method=AuthMethodType.TON_WALLET,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TON auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/link-wallet", response_model=dict)
async def link_wallet(
    request: UnifiedAuthRequest,
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
        await UnifiedUserService.link_ton_wallet_to_user(
            db=db,
            user_id=current_user.id,
            wallet_address=request.wallet_address,
            wallet_metadata=request.ton_wallet_metadata,
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
        logger.error(f"Link wallet error: {str(e)}")
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
