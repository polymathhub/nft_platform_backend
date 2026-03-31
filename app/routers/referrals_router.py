"""
Simple Referral Code Management
- Generate unique referral codes per user
- Get referral code and stats
- Stateless (no referral tracking in this version)
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db_session
from app.models import User
from app.schemas.user import UserResponse
from app.utils.telegram_auth_dependency import get_current_user
from app.utils.referral_utils import generate_referral_code
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/referrals", tags=["referrals"])


class ReferralResponse(BaseModel):
    """Referral info response"""
    referral_code: str
    referral_url: str
    total_referrals: int
    
    class Config:
        from_attributes = True


# ============================================================================
# ENDPOINT 1: Get Current User's Referral Code
# ============================================================================
@router.get("/me", response_model=dict, summary="Get User's Referral Code")
async def get_my_referral(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get the current user's referral code.
    
    If user doesn't have a code yet, generate one.
    
    Returns:
        {
            "success": true,
            "data": {
                "referral_code": "REF_ABC123XYZ",
                "referral_url": "https://t.me/nftbot?startapp=ref_ABC123XYZ",
                "total_referrals": 5
            }
        }
    """
    try:
        # If user doesn't have a referral code, generate one
        if not current_user.referral_code:
            current_user.referral_code = await generate_referral_code(db)
            await db.flush()
            await db.commit()
            await db.refresh(current_user)
            logger.info(f"Generated referral code for user {current_user.id}")

        # Count referrals (users who were referred by this user)
        query = select(func.count(User.id)).where(
            User.referred_by_id == current_user.id
        )
        result = await db.execute(query)
        referral_count = result.scalar() or 0

        # Build referral URL (for Telegram mini app)
        referral_url = f"https://t.me/nftplatform_bot?startapp=ref_{current_user.referral_code}"

        return {
            "success": True,
            "data": {
                "referral_code": current_user.referral_code,
                "referral_url": referral_url,
                "total_referrals": referral_count
            },
            "message": "Referral code retrieved successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to get referral code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve referral code"
        )


# ============================================================================
# ENDPOINT 2: Regenerate Referral Code (if needed)
# ============================================================================
@router.post("/regenerate", response_model=dict, summary="Regenerate Referral Code")
async def regenerate_referral(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Generate a new referral code for the user.
    
    Use this if user wants a different code.
    """
    try:
        # Generate new code
        current_user.referral_code = await generate_referral_code(db)
        await db.flush()
        await db.commit()
        await db.refresh(current_user)
        
        logger.info(f"Regenerated referral code for user {current_user.id}")

        # Count referrals
        query = select(func.count(User.id)).where(
            User.referred_by_id == current_user.id
        )
        result = await db.execute(query)
        referral_count = result.scalar() or 0

        referral_url = f"https://t.me/nftplatform_bot?startapp=ref_{current_user.referral_code}"

        return {
            "success": True,
            "data": {
                "referral_code": current_user.referral_code,
                "referral_url": referral_url,
                "total_referrals": referral_count
            },
            "message": "Referral code regenerated successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to regenerate referral code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate referral code"
        )


# ============================================================================
# ENDPOINT 3: Use Referral Code (when new user signs up)
# ============================================================================
@router.post("/use/{referral_code}", response_model=dict, summary="Apply Referral Code")
async def use_referral_code(
    referral_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    A new user can apply a referral code when signing up.
    
    This links the new user to the referrer.
    """
    try:
        # Check if user already has a referrer
        if current_user.referred_by_id is not None:
            return {
                "success": False,
                "data": None,
                "message": "You already have a referrer"
            }

        # Find the referrer by referral code
        query = select(User).where(User.referral_code == referral_code)
        result = await db.execute(query)
        referrer = result.scalar_one_or_none()

        if not referrer:
            return {
                "success": False,
                "data": None,
                "message": "Invalid referral code"
            }

        if referrer.id == current_user.id:
            return {
                "success": False,
                "data": None,
                "message": "Cannot use your own referral code"
            }

        # Link new user to referrer
        current_user.referred_by_id = referrer.id
        await db.flush()
        await db.commit()

        logger.info(f"User {current_user.id} applied referral code from {referrer.id}")

        return {
            "success": True,
            "data": {
                "referrer": referrer.username,
                "message": f"Welcome! You've been referred by {referrer.username}"
            },
            "message": "Referral code applied successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to apply referral code: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply referral code"
        )
