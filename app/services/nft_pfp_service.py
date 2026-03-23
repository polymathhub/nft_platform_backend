"""
NFT PFP Service

Business logic for managing NFT profile pictures.
Handles setting, retrieving, and removing NFTs as user profile pictures.
"""

import logging
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import User, NFT
from app.schemas.nft_pfp import NFTPFPResponse

logger = logging.getLogger(__name__)


class NFTPFPService:
    """Service for managing NFT Profile Pictures"""

    @staticmethod
    async def set_nft_as_pfp(
        db: AsyncSession,
        user_id: UUID,
        nft_id: UUID,
    ) -> Tuple[Optional[NFT], Optional[str]]:
        """
        Set an NFT as the user's profile picture.
        
        Args:
            db: Database session
            user_id: ID of the user
            nft_id: ID of the NFT to set as PFP
            
        Returns:
            Tuple of (NFT or None, error_message or None)
        """
        try:
            # Verify the NFT exists and belongs to the user
            nft_stmt = select(NFT).where(
                (NFT.id == nft_id) & (NFT.user_id == user_id)
            )
            result = await db.execute(nft_stmt)
            nft = result.scalar_one_or_none()
            
            if not nft:
                return None, f"NFT not found or does not belong to user"
            
            # Check if NFT is locked (can't use locked NFTs as PFP)
            if nft.is_locked:
                return None, "Cannot set locked NFT as profile picture"
            
            # Update the user's nft_pfp_id
            user_stmt = select(User).where(User.id == user_id)
            result = await db.execute(user_stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return None, "User not found"
            
            user.nft_pfp_id = nft_id
            await db.commit()
            
            logger.info(f"✓ User {user_id} set NFT {nft_id} as PFP")
            return nft, None
            
        except Exception as e:
            await db.rollback()
            logger.error(f"✗ Error setting NFT as PFP: {str(e)}")
            return None, f"Error setting NFT as PFP: {str(e)}"

    @staticmethod
    async def remove_nft_pfp(
        db: AsyncSession,
        user_id: UUID,
    ) -> Tuple[bool, Optional[str]]:
        """
        Remove NFT as the user's profile picture.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            Tuple of (success, error_message or None)
        """
        try:
            user_stmt = select(User).where(User.id == user_id)
            result = await db.execute(user_stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return False, "User not found"
            
            if user.nft_pfp_id is None:
                return False, "No NFT is currently set as PFP"
            
            user.nft_pfp_id = None
            await db.commit()
            
            logger.info(f"✓ Removed PFP for user {user_id}")
            return True, None
            
        except Exception as e:
            await db.rollback()
            logger.error(f"✗ Error removing PFP: {str(e)}")
            return False, f"Error removing PFP: {str(e)}"

    @staticmethod
    async def get_user_pfp(
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[NFTPFPResponse]:
        """
        Get the user's current NFT PFP.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            NFTPFPResponse if PFP is set, None otherwise
        """
        try:
            # Get the user with their PFP NFT loaded
            user_stmt = select(User).where(User.id == user_id).options(
                joinedload(User.nft_pfp_rel)
            )
            result = await db.execute(user_stmt)
            user = result.unique().scalar_one_or_none()
            
            if not user or not user.nft_pfp_id:
                return None
            
            # The relationship should be loaded, but return it as schema
            if hasattr(user, 'nft_pfp_rel') and user.nft_pfp_rel:
                return NFTPFPResponse.model_validate(user.nft_pfp_rel)
            
            # Fallback: load the NFT directly
            nft_stmt = select(NFT).where(NFT.id == user.nft_pfp_id)
            result = await db.execute(nft_stmt)
            nft = result.scalar_one_or_none()
            
            if nft:
                return NFTPFPResponse.model_validate(nft)
            
            return None
            
        except Exception as e:
            logger.error(f"✗ Error getting user PFP: {str(e)}")
            return None

    @staticmethod
    async def get_user_with_pfp(
        db: AsyncSession,
        user_id: UUID,
    ):
        """
        Get user with their PFP NFT details loaded.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            User object with PFP relationship loaded
        """
        try:
            user_stmt = select(User).where(User.id == user_id).options(
                joinedload(User.nft_pfp_rel)
            )
            result = await db.execute(user_stmt)
            user = result.unique().scalar_one_or_none()
            return user
            
        except Exception as e:
            logger.error(f"✗ Error getting user with PFP: {str(e)}")
            return None
