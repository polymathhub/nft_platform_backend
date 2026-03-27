import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session
from app.models import User
from app.schemas.user import UserResponse
from app.utils.telegram_auth_dependency import get_current_user
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["user"])

class UserUpdateRequest(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_creator: Optional[bool] = None
    bio: Optional[str] = None
    creator_bio: Optional[str] = None

@router.post("/update", response_model=dict, summary="Update User Profile")
async def update_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Update user profile information.
    
    Only authenticated users can update their own profile.
    
    Args:
        update_data: Fields to update (full_name, avatar_url, is_creator)
    
    Returns:
        Updated user profile
    """
    try:
        # Update only provided fields
        if update_data.full_name is not None:
            current_user.full_name = update_data.full_name
        if update_data.avatar_url is not None:
            current_user.avatar_url = update_data.avatar_url
        if update_data.is_creator is not None:
            current_user.is_creator = update_data.is_creator
        if update_data.bio is not None:
            current_user.creator_bio = update_data.bio
        if update_data.creator_bio is not None:
            current_user.creator_bio = update_data.creator_bio
        
        # Commit changes
        await db.flush()
        await db.commit()
        await db.refresh(current_user)
        
        return {
            "success": True,
            "data": UserResponse.model_validate(current_user),
            "message": "User profile updated successfully"
        }
    except Exception as e:
        logger.error(f"Failed to update user profile: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

@router.get("/profile", response_model=dict, summary="Get User Profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    return {
        "success": True,
        "data": UserResponse.model_validate(current_user),
        "message": "User profile retrieved successfully"
    }
@router.get("/info", response_model=dict, summary="Get User Info")
async def get_user_info(current_user: User = Depends(get_current_user)):
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
