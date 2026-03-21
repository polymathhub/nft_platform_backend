"""
ME ENDPOINT - Current User Identity (Telegram-based)

GET /api/v1/me
- Returns authenticated user data
- Uses ONLY Telegram initData verification
- No tokens, no sessions

This replaces the old:
- /api/auth/profile (JWT-based)
- /api/v1/auth/profile (JWT-based)
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models import User
from app.schemas.user import UserResponse
from app.utils.telegram_auth_dependency import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["identity"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current authenticated user.
    
    ✅ Authentication:
    - Reads: X-Telegram-Init-Data header
    - Verifies: HMAC-SHA256 signature
    - Returns: User data
    
    ✅ Behavior:
    - Auto-registers new Telegram users
    - No password needed
    - No token refresh needed
    
    ✅ Status Codes:
    - 200: Success - user data returned
    - 401: Unauthorized - invalid/missing Telegram data
    - 500: Server error
    
    Example:
    ```
    curl -H "X-Telegram-Init-Data: user=%7B..." /api/v1/me
    ```
    
    Response:
    ```json
    {
      "id": "user_123",
      "email": "tg_123456789@telegram.local",
      "username": "john_doe",
      "full_name": "John Doe",
      "telegram_id": "123456789",
      "telegram_username": "johndoe",
      "is_active": true,
      ...
    }
    ```
    """
    if not current_user:
        logger.error("[API] /me called but get_current_user returned None")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    logger.debug(f"[API] GET /me - user_id={current_user.id}, username={current_user.username}")
    
    return current_user


@router.post("/me/refresh", response_model=UserResponse)
async def refresh_user_endpoint(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Refresh current user data.
    
    (This endpoint is for compatibility - in reality, just re-send initData)
    
    Deprecated: With Telegram auth, just call /api/v1/me again with fresh initData.
    No refresh tokens needed.
    
    Returns: Current user data
    """
    logger.debug(f"[API] POST /me/refresh - user_id={current_user.id}")
    return current_user


@router.get("/me/logout", response_model=dict)
async def logout_endpoint() -> dict:
    """
    Logout endpoint.
    
    With Telegram auth, logout is client-side only:
    - Clear any local app state
    - Clear Telegram WebApp data (if possible)
    - Backend has nothing to clear (stateless)
    
    Returns: Success message
    """
    logger.debug("[API] GET /me/logout - stateless logout")
    
    return {
        "success": True,
        "message": "Logged out successfully (stateless - nothing to clear on server)",
        "next_action": "Refresh page or reopen Telegram Mini App"
    }


@router.get("/profile", response_model=UserResponse)
async def get_profile_compat(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Compatibility endpoint - routes old /api/v1/profile calls to /api/v1/me.
    
    Legacy support only. New code should use /api/v1/me.
    """
    return current_user
