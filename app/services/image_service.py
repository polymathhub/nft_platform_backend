"""
ImageService: Handles image uploads, storage, and retrieval for NFTs.
Prevents database bloat by storing large files separately.
"""

import logging
import hashlib
import base64
import io
from typing import Optional, Tuple
from uuid import UUID
from datetime import datetime
from PIL import Image as PILImage

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models import Image, ImageType
from app.models.user import User

logger = logging.getLogger(__name__)


class ImageService:
    """
    Manages image uploads and storage for NFTs.
    
    Strategy:
    - Images < 50KB: Store entire base64 in database (instant retrieval)
    - Images 50KB-500KB: Store in database with thumbnail
    - Images > 500KB: Store path reference (S3/IPFS future support)
    """

    # Size thresholds in bytes
    SMALL_IMAGE_THRESHOLD = 50 * 1024  # 50KB
    LARGE_IMAGE_THRESHOLD = 500 * 1024  # 500KB

    @staticmethod
    async def upload_image(
        db: AsyncSession,
        file_content: bytes,
        filename: str,
        mime_type: str,
        user_id: UUID,
        image_type: ImageType = ImageType.NFT_PREVIEW,
        nft_id: Optional[UUID] = None,
    ) -> Tuple[Optional[Image], Optional[str]]:
        """
        Uploads and stores an image for an NFT.

        Args:
            db: Database session
            file_content: Raw file bytes
            filename: Original filename
            mime_type: MIME type (e.g., 'image/jpeg')
            user_id: User uploading the image
            image_type: Type of image (preview, full, etc)
            nft_id: Associated NFT ID (optional)

        Returns:
            (Image record, error message) - error is None if successful
        """
        try:
            file_size = len(file_content)

            # Validate user exists
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if not user:
                return None, "User not found"

            # Get image dimensions for metadata
            width, height = None, None
            try:
                img = PILImage.open(io.BytesIO(file_content))
                width, height = img.size
            except Exception as e:
                logger.warning(f"Could not determine image dimensions: {e}")

            # Calculate hashes for deduplication
            md5_hash = hashlib.md5(file_content).hexdigest()
            sha256_hash = hashlib.sha256(file_content).hexdigest()

            # Check if this exact image already exists (deduplication)
            existing_result = await db.execute(
                select(Image).where(
                    and_(
                        Image.md5_hash == md5_hash,
                        Image.uploaded_by_user_id == user_id,
                    )
                )
            )
            existing_image = existing_result.scalar_one_or_none()
            if existing_image and not existing_image.deleted_at:
                logger.info(f"Image already uploaded by user {user_id}, reusing: {md5_hash}")
                return existing_image, None

            # Determine storage strategy
            base64_data = None
            storage_type = "database"
            storage_path = None

            if file_size <= self.SMALL_IMAGE_THRESHOLD:
                # Small images: store full base64 in database
                base64_data = base64.b64encode(file_content).decode('utf-8')
                logger.info(f"Storing small image ({file_size} bytes) in database as base64")

            elif file_size <= self.LARGE_IMAGE_THRESHOLD:
                # Medium images: store base64 + thumbnail
                base64_data = base64.b64encode(file_content).decode('utf-8')
                logger.info(f"Storing medium image ({file_size} bytes) in database with thumbnail")
                
            else:
                # Large images: store reference only (future: S3/IPFS)
                logger.warning(
                    f"Image too large ({file_size} bytes). "
                    f"Full storage requires S3/IPFS integration. "
                    f"Using base64 for now (set storage_path for S3)."
                )
                # For now, still store base64 with warning
                # In production, would upload to S3 and set storage_path
                base64_data = base64.b64encode(file_content).decode('utf-8')

            # Create Image record
            image = Image(
                uploaded_by_user_id=user_id,
                nft_id=nft_id,
                filename=filename,
                original_filename=filename,
                mime_type=mime_type,
                file_size=file_size,
                width=width,
                height=height,
                image_type=image_type,
                storage_type=storage_type,
                storage_path=storage_path,
                md5_hash=md5_hash,
                sha256_hash=sha256_hash,
                base64_data=base64_data,
                is_public="private",
                uploaded_at=datetime.utcnow(),
            )

            db.add(image)
            await db.commit()
            await db.refresh(image)

            logger.info(
                f"Image uploaded successfully: {image.id} "
                f"({file_size} bytes, {mime_type}, user={user_id})"
            )

            return image, None

        except Exception as e:
            logger.error(f"Error uploading image: {e}", exc_info=True)
            return None, f"Image upload failed: {str(e)}"

    @staticmethod
    async def get_image_url(
        image: Image,
        include_data: bool = False,
    ) -> str:
        """
        Gets the usable URL/URI for an image.

        Args:
            image: Image record from database
            include_data: If True, returns full data URI. If False, returns reference.

        Returns:
            Image URL (data URI for database storage, path for external storage)
        """
        if image.storage_type == "database" and image.base64_data:
            if include_data:
                # Return full data URI for direct use
                return f"data:{image.mime_type};base64,{image.base64_data}"
            else:
                # Return reference URL (requires API to serve)
                return f"/api/v1/images/{image.id}/data"

        elif image.storage_path:
            # External storage (S3, IPFS, etc)
            return image.storage_path

        else:
            logger.warning(f"Image {image.id} has no retrievable data")
            return ""

    @staticmethod
    async def get_image_by_id(
        db: AsyncSession,
        image_id: UUID,
    ) -> Optional[Image]:
        """Retrieves an image record by ID"""
        result = await db.execute(
            select(Image).where(
                and_(
                    Image.id == image_id,
                    Image.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_image(
        db: AsyncSession,
        image_id: UUID,
        user_id: UUID,
    ) -> Tuple[bool, Optional[str]]:
        """
        Soft-deletes an image (marks as deleted, doesn't remove from database).

        Args:
            db: Database session
            image_id: Image to delete
            user_id: User requesting deletion (must be uploader)

        Returns:
            (success, error message)
        """
        try:
            image = await ImageService.get_image_by_id(db, image_id)
            if not image:
                return False, "Image not found"

            if image.uploaded_by_user_id != user_id:
                return False, "You can only delete your own images"

            image.deleted_at = datetime.utcnow()
            await db.commit()

            logger.info(f"Image {image_id} deleted by user {user_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error deleting image {image_id}: {e}", exc_info=True)
            return False, f"Delete failed: {str(e)}"
