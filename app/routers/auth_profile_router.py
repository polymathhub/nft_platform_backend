"""
Authentication Profile Endpoints

Provides the following endpoints:
- GET /api/auth/profile - Get current user profile (authenticated)
- GET /api/auth/check - Check authentication status (optional auth)
- POST /api/auth/logout - Logout endpoint (stateless)
- GET /api/auth/me - Alias for /api/auth/profile
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models import User
from app.schemas.user import UserResponse
from app.utils.telegram_auth_dependency import get_current_user, get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/profile", response_model=dict, summary="Get User Profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get current authenticated user profile.
    
    Requires Authorization header with valid JWT token.
    
    Args:
        current_user: Current authenticated user (from JWT token)
    
    Returns:
        User profile data
    
    Status Codes:
        - 200: Success
        - 401: Unauthorized (missing or invalid token)
    
    Example:
    ```bash
    curl -X GET http://localhost:8000/api/auth/profile \\
      -H "Authorization: Bearer YOUR_TOKEN_HERE"
    ```
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized"
        )
    
    logger.debug(f"[API] GET /api/auth/profile - user_id={current_user.id}, username={current_user.username}")
    
    return {
        "success": True,
        "user": UserResponse.model_validate(current_user),
        "authenticated": True
    }


@router.get("/me", response_model=dict, summary="Get Current User (Alias for /profile)")
async def get_me(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get current authenticated user profile (alias for /api/auth/profile).
    
    Requires Authorization header with valid JWT token.
    
    Returns:
        User profile data
    
    Status Codes:
        - 200: Success
        - 401: Unauthorized (missing or invalid token)
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized"
        )
    
    logger.debug(f"[API] GET /api/auth/me - user_id={current_user.id}")
    
    return {
        "success": True,
        "user": UserResponse.model_validate(current_user),
        "authenticated": True
    }


@router.post("/logout", response_model=dict, summary="Logout User")
async def logout() -> dict:
    """
    Logout endpoint.
    
    With JWT-based stateless authentication, logout is client-side only:
    - Frontend must clear localStorage tokens
    - Backend has nothing to invalidate (stateless)
    
    Returns:
        Success message
    
    Example:
    ```bash
    curl -X POST http://localhost:8000/api/auth/logout \\
      -H "Authorization: Bearer YOUR_TOKEN_HERE"
    ```
    """
    logger.debug("[API] POST /api/auth/logout - stateless logout")
    
    return {
        "success": True,
        "message": "Logged out successfully. Clear localStorage tokens on frontend.",
        "next_action": "Clear localStorage.token and localStorage.refresh_token"
    }


@router.get("/check", response_model=dict, summary="Check Authentication Status")
async def check_auth(
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> dict:
    """
    Check current authentication status.
    
    Does NOT require authentication - can be called without token.
    
    Returns:
        - authenticated=true + user info if token is valid
        - authenticated=false if no token or invalid token
    
    Status Codes:
        - 200: Always returns 200 (even if not authenticated)
    
    Example:
    ```bash
    # With valid token
    curl -X GET http://localhost:8000/api/auth/check \\
      -H "X-Telegram-Init-Data: YOUR_TELEGRAM_DATA"
    # Response: {"authenticated": true, "user_id": "123", ...}
    
    # Without token
    curl -X GET http://localhost:8000/api/auth/check
    # Response: {"authenticated": false}
    ```
    """
    logger.debug("[API] GET /api/auth/check")
    
    if current_user:
        logger.debug(f"[API] Auth check: authenticated user_id={current_user.id}")
        return {
            "authenticated": True,
            "user_id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "telegram_id": current_user.telegram_id
        }
    else:
        logger.debug("[API] Auth check: not authenticated")
        return {
            "authenticated": False
        }
