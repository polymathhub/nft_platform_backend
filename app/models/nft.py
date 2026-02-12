from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum, Index, Text, Integer, JSON, Float
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database import Base
from app.database.types import GUID


class NFTStatus(str, PyEnum):

    PENDING = "pending"
    MINTED = "minted"
    TRANSFERRED = "transferred"
    LOCKED = "locked"
    BURNED = "burned"


class NFTLockReason(str, PyEnum):

    MARKETPLACE = "marketplace"
    STAKING = "staking"
    BRIDGE = "bridge"
    CUSTOM = "custom"


class RarityTier(str, PyEnum):

    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class NFT(Base):

    __tablename__ = "nfts"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    global_nft_id = Column(String(255), unique=True, nullable=False)  # unique=True creates index automatically
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    wallet_id = Column(
        GUID(),
        ForeignKey("wallets.id"),
        nullable=False,
        index=True,
    )
    collection_id = Column(
        GUID(),
        ForeignKey("collections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    blockchain = Column(String(50), nullable=False)
    contract_address = Column(String(255), nullable=True)
    token_id = Column(String(255), nullable=True, index=True)
    mint_address = Column(String(255), nullable=True)
    owner_address = Column(String(255), nullable=False)
    status = Column(
        Enum(NFTStatus),
        default=NFTStatus.PENDING,
        nullable=False,
    )
    is_locked = Column(Boolean, default=False, nullable=False)
    lock_reason = Column(String(50), nullable=True)
    locked_until = Column(DateTime, nullable=True)
    ipfs_hash = Column(String(255), nullable=True)
    image_url = Column(String(500), nullable=True)
    media_type = Column(String(50), nullable=True)
    royalty_percentage = Column(Integer, default=0, nullable=False)
    
    # Rarity and attributes
    attributes = Column(JSON, nullable=True, default={})  # {trait_name: trait_value, ...}
    rarity_score = Column(Float, nullable=True, default=None)  # 0-100 score
    rarity_tier = Column(
        Enum(RarityTier),
        nullable=True,
        default=None,
    )
    
    nft_metadata = Column(JSON, nullable=True, default={})
    transaction_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    minted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_nfts_user_blockchain", "user_id", "blockchain"),
        Index("ix_nfts_contract_token", "contract_address", "token_id"),
        Index("ix_nfts_owner", "owner_address"),
        Index("ix_nfts_is_locked", "is_locked"),
        Index("ix_nfts_collection", "collection_id"),
        Index("ix_nfts_rarity_tier", "rarity_tier"),
        Index("ix_nfts_rarity_score", "rarity_score"),
    )

    def __repr__(self) -> str:
        return f"<NFT(id={self.id}, name={self.name}, blockchain={self.blockchain}, token_id={self.token_id})>"
