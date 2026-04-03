"""
Blockchain Transaction Verification Model

Stores on-chain transaction data with verification status
Separate from DB-only transactions for truth-seeking
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Enum, Text, Integer, Boolean
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database.base_class import Base
from app.database.types import GUID


class BlockchainTransactionStatus(str, PyEnum):
    """Tracks on-chain confirmation status"""
    PENDING = "pending"  # Submitted to mempool
    IN_PROGRESS = "in_progress"  # 1-50 confirmations
    CONFIRMED = "confirmed"  # 51+ confirmations
    FAILED = "failed"  # Rejected by network
    NOT_FOUND = "not_found"  # Lost in mempool


class BlockchainTransaction(Base):
    """Track on-chain transactions with verification data"""
    
    __tablename__ = "blockchain_transactions"
    
    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    
    # Link to user and wallet
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    wallet_address = Column(
        String(255),
        nullable=False,
        index=True,
    )
    
    # Link to NFT (if relevant)
    related_nft_id = Column(
        GUID(),
        ForeignKey("nfts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Transaction hash - source of truth
    transaction_hash = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # Transaction details
    from_address = Column(String(255), nullable=False, index=True)
    to_address = Column(String(255), nullable=False)
    
    # CRITICAL: Smart contract address being called
    contract_address = Column(
        String(255),
        nullable=True,
        index=True,
    )
    
    # Amount in nanoTON (integer for precision)
    amount_nano_ton = Column(
        String(50),  # Use string to avoid overflow
        nullable=False,
    )
    
    # Transaction type
    transaction_type = Column(
        String(50),
        nullable=False,
    )
    
    # CRITICAL: BOC payload for verification
    payload_boc = Column(
        Text,
        nullable=True,
    )
    
    # Blockchain state
    status = Column(
        Enum(BlockchainTransactionStatus),
        default=BlockchainTransactionStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    # Confirmation tracking
    confirmations = Column(
        Integer,
        default=0,
        nullable=False,
    )
    
    block_number = Column(
        String(50),
        nullable=True,
    )
    
    block_time = Column(
        DateTime,
        nullable=True,
    )
    
    # Trust and verification
    trust_level = Column(
        Integer,
        default=0,  # 0-10 scale
        nullable=False,
    )
    
    verified_at = Column(
        DateTime,
        nullable=True,
    )
    
    verification_attempts = Column(
        Integer,
        default=0,
        nullable=False,
    )
    
    last_verification_at = Column(
        DateTime,
        nullable=True,
    )
    
    # Error tracking
    error_reason = Column(
        Text,
        nullable=True,
    )
    
    # Metadata
    tx_metadata = Column(
        String(4000),  # JSON stringified
        nullable=True,
        default="{}",
    )
    
    # Immutable record of what was sent
    submitted_payload = Column(
        Text,
        nullable=True,
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    
    submitted_at = Column(
        DateTime,
        nullable=True,
    )
    
    confirmed_at = Column(
        DateTime,
        nullable=True,
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    __table_args__ = (
        Index("ix_blockchain_tx_user", "user_id", "created_at"),
        Index("ix_blockchain_tx_wallet", "wallet_address", "status"),
        Index("ix_blockchain_tx_hash", "transaction_hash"),
        Index("ix_blockchain_tx_contract", "contract_address"),
        Index("ix_blockchain_tx_nft", "related_nft_id"),
    )
    
    def __repr__(self) -> str:
        return f"<BlockchainTransaction(hash={self.transaction_hash}, status={self.status}, confirmations={self.confirmations})>"
