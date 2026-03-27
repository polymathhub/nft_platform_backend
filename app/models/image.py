"""
Image storage model for NFT media files.
Decouples image storage from NFT records and prevents base64 data URI bloat in database.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, LargeBinary, Enum, Index
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database.base_class import Base
from app.database.types import GUID


class ImageType(str, PyEnum):
    """Categorizes images for different purposes"""
    NFT_PREVIEW = "nft_preview"
    NFT_FULL = "nft_full"
    COLLECTION_COVER = "collection_cover"
    USER_AVATAR = "user_avatar"
    MARKETPLACE_THUMB = "marketplace_thumb"


class Image(Base):
    """
    Stores image data and metadata separately from NFTs.
    This allows:
    - Reuse of images across multiple NFTs (e.g., placeholder, default covers)
    - Proper file storage with versioning capabilities
    - Fast database lookups without base64 bloat
    - Easy cache invalidation and CDN serving
    """

    __tablename__ = "images"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    # Who uploaded this image
    uploaded_by_user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional: Which NFT is this the primary image for
    nft_id = Column(
        GUID(),
        ForeignKey("nfts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # File metadata
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)  # Name from user's upload
    mime_type = Column(String(50), nullable=False)  # e.g., 'image/jpeg'
    file_size = Column(Integer, nullable=False)  # Size in bytes
    width = Column(Integer, nullable=True)  # Image dimensions
    height = Column(Integer, nullable=True)

    # Image type/category for organization
    image_type = Column(
        Enum(ImageType),
        default=ImageType.NFT_PREVIEW,
        nullable=False,
        index=True,
    )

    # Storage strategy (for future expansion to S3, IPFS, etc)
    storage_type = Column(String(50), default="database", nullable=False)  # 'database', 's3', 'ipfs'
    storage_path = Column(String(500), nullable=True)  # S3 key, IPFS hash, or local path

    # Checksums for deduplication and integrity
    md5_hash = Column(String(32), nullable=True, unique=True, index=True)  # For dedup
    sha256_hash = Column(String(64), nullable=True, unique=True, index=True)

    # Privacy and access control
    is_public = Column(String(50), default="private", nullable=False)  # 'public', 'private', 'shared'
    access_token = Column(String(64), nullable=True, unique=True, index=True)  # For private share links

    # Base64 data (for small images only)
    # For large files, this remains NULL and storage_path is used instead
    base64_data = Column(String(2097152), nullable=True)  # Max ~2MB base64 (~1.5MB raw)
    base64_thumbnail = Column(String(100000), nullable=True)  # Thumbnail for quick loading

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # For temporary images

    # Deletion soft-delete support
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_images_user_type", "uploaded_by_user_id", "image_type"),
        Index("ix_images_nft", "nft_id"),
        Index("ix_images_public", "is_public"),
    )

    def __repr__(self) -> str:
        return f"<Image(id={self.id}, filename={self.filename}, type={self.image_type})>"
