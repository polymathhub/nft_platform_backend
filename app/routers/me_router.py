"""
Simple /api/user/me endpoint for frontend profile fetching
Works with JWT tokens from Telegram auth
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import User
from app.utils.auth import get_current_user
from app.schemas.user import UserResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/user", tags=["user-simple"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user profile.
    
    Requires: Authorization: Bearer {token}
    
    Returns: User profile data
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    logger.info(f"[API] GET /api/user/me - user_id={current_user.id}")
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout endpoint (frontend should clear token on client-side)"""
    return {"success": True, "message": "Logout successful"}
