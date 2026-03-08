"""
User endpoints - Compatibility layer for web app.
Provides user profile and data endpoints for frontend applications.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session
from app.models import User
from app.schemas.user import UserResponse
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["user"])


@router.get("/profile", response_model=dict, summary="Get User Profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get current user profile with all user data.
    
    Used by web app to fetch user information including:
    - username
    - email
    - avatar_url (profile picture)
    - user_id
    - telegram information if authenticated
    
    Returns:
    {
        "success": true,
        "data": {
            "id": "user-uuid",
            "username": "username",
            "email": "user@example.com",
            "avatar_url": "https://...",
            "telegram_id": "...",
            "telegram_username": "...",
            ...
        }
    }
    """
    return {
        "success": True,
        "data": UserResponse.model_validate(current_user),
        "message": "User profile retrieved successfully"
    }


@router.get("/info", response_model=dict, summary="Get User Info")
async def get_user_info(current_user: User = Depends(get_current_user)):
    """
    Get basic user information.
    Simplified version of profile endpoint.
    """
    return {
        "success": True,
        "data": {
            "id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "avatar_url": current_user.avatar_url,
            "is_creator": current_user.is_creator,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        }
    }
