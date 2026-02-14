from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum, Index, JSON
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database import Base
from app.database.types import GUID


class BlockchainType(str, PyEnum):

    # Layer 1 Blockchains
    TON = "ton"
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    BITCOIN = "bitcoin"
    AVALANCHE = "avalanche"
    
    # Layer 2 / Sidechains
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"


class WalletType(str, PyEnum):

    CUSTODIAL = "custodial"
    SELF_CUSTODY = "self_custody"


class Wallet(Base):

    __tablename__ = "wallets"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    blockchain = Column(
        Enum(BlockchainType),
        nullable=False,
    )
    wallet_type = Column(
        Enum(WalletType),
        default=WalletType.CUSTODIAL,
        nullable=False,
    )
    address = Column(String(255), unique=True, nullable=False)
    public_key = Column(String(500), nullable=True)
    encrypted_private_key = Column(String(1000), nullable=True)
    encrypted_mnemonic = Column(String(1000), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    wallet_metadata = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_wallets_user_blockchain", "user_id", "blockchain"),
        Index("ix_wallets_address", "address"),
    )

    def __repr__(self) -> str:
        return f"<Wallet(id={self.id}, user_id={self.user_id}, blockchain={self.blockchain}, address={self.address})>"
