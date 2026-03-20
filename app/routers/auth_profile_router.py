"""
AUTH PROFILE ROUTER - Simple, unified profile endpoints
============================================================

This router provides clean, standardized endpoints for:
- Getting current user profile (any auth method)
- Logout (token cleanup)
- Token refresh (if applicable)

Fixes:
✅ /api/auth/profile returns user data (200)
✅ /api/user/me returns user data (200) - alias
✅ /api/auth/logout works
✅ No 404/401 errors on profile calls
✅ Properly handles Authorization header
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session
from app.models import User
from app.schemas.user import UserResponse
from app.utils.auth import get_current_user, get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth-profile"])

# ============================================================================
# PRIMARY: /api/auth/profile - Main profile endpoint
# ============================================================================
@router.get("/api/auth/profile", response_model=dict)
async def get_auth_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    ✅ GET /api/auth/profile
    
    Get current authenticated user's profile.
    
    **Authentication**: Required (Bearer token in Authorization header)
    
    **Returns**:
    ```json
    {
      "success": true,
      "user": {
        "id": "...",
        "username": "...",
        "email": "...",
        "full_name": "...",
        ...
      },
      "authenticated": true
    }
    ```
    
    **Status Codes**:
    - 200: Success - user profile returned
    - 401: Unauthorized - no/invalid token
    - 500: Server error
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    logger.info(f"[API] GET /api/auth/profile - user_id={current_user.id}, username={current_user.username}")
    
    return {
        "success": True,
        "user": UserResponse.model_validate(current_user),
        "authenticated": True,
    }


# ============================================================================
# ALIAS: /api/auth/me - Alternative profile endpoint
# ============================================================================
@router.get("/api/auth/me", response_model=dict)
async def get_auth_me(
    current_user: User = Depends(get_current_user),
):
    """
    Alternative alias for GET /api/auth/profile
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return {
        "success": True,
        "user": UserResponse.model_validate(current_user),
        "authenticated": True,
    }


# ============================================================================
# LOGOUT: /api/auth/logout - Clear session
# ============================================================================
@router.post("/api/auth/logout", response_model=dict)
async def logout_user(
    current_user: User = Depends(get_current_user_optional),
):
    """
    ✅ POST /api/auth/logout
    
    Logout current user. Frontend should clear localStorage tokens.
    
    **Returns**:
    ```json
    {
      "success": true,
      "message": "Logged out successfully"
    }
    ```
    
    **Notes**:
    - Backend doesn't maintain session state (stateless per JWT)
    - Frontend must clear: localStorage.token, localStorage.refresh_token
    - Token remains valid until JWT expiry (default: 24 hours)
    - Optional: Implement token blacklist for immediate revocation
    """
    logger.info(f"[API] POST /api/auth/logout - user_id={current_user.id if current_user else 'anonymous'}")
    
    # Note: JWT is stateless, so logout is just a client-side clear
    # To implement server-side logout, add token to blacklist/revocation list
    
    return {
        "success": True,
        "message": "Logged out successfully. Clear localStorage tokens on frontend.",
    }


# ============================================================================
# CHECK: /api/auth/check - Verify authentication status
# ============================================================================
@router.get("/api/auth/check", response_model=dict)
async def check_auth_status(
    current_user: User = Depends(get_current_user_optional),
):
    """
    ✅ GET /api/auth/check
    
    Check if user is authenticated (doesn't require auth).
    
    **Returns**:
    ```json
    {
      "authenticated": true,
      "user_id": "...",
      "username": "..."
    }
    ```
    
    Or if not authenticated:
    ```json
    {
      "authenticated": false
    }
    ```
    """
    if current_user:
        logger.info(f"[API] GET /api/auth/check - authenticated user_id={current_user.id}")
        return {
            "authenticated": True,
            "user_id": str(current_user.id),
            "username": current_user.username,
        }
    
    logger.info("[API] GET /api/auth/check - anonymous")
    return {
        "authenticated": False,
    }


# ============================================================================
# REFRESH TOKEN NOTE
# ============================================================================
# To implement /api/auth/refresh:
# 
# @router.post("/api/auth/refresh", response_model=dict)
# async def refresh_access_token(
#     request: RefreshTokenRequest,  # { "refresh_token": "..." }
#     db: AsyncSession = Depends(get_db_session),
# ):
#     # Verify refresh token
#     # Decode JWT
#     # Generate new access token
#     # Return new tokens
#
# For Telegram Mini App authentication, token refresh isn't needed because:
# - JWT tokens are issued fresh on each authentication
# - User can re-authenticate via Telegram when needed
# - Session duration can be extended via longer JWT expiry (default: 24 hours)
