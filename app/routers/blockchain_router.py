"""
Production-Grade Blockchain Operations Router

Handles:
- NFT mint preparation (payload generation, metadata upload)
- NFT mint confirmation (on-chain verification)
- Transaction verification
- Session management
- TON Connect wallet integration

These endpoints bridge frontend wallet connection with backend blockchain logic.
Compatible with Telegram Web App SDK and TON Connect UI.
"""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.security import get_current_user
from app.models import User, BlockchainTransaction, BlockchainTransactionStatus
from app.database import get_db_session
from app.services.ton_contracts import NFTContractPayloads
from app.services.nft_metadata import NFTMetadataService
from app.services.tonconnect_integration import (
    TONConnectTransaction,
    TONConnectCallback,
    TONConnectWalletSync,
)
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/blockchain", tags=["blockchain"])


# ═══════════════════════════════════════════════════════════════
# REQUEST/RESPONSE SCHEMAS - Telegram SDK & TON Connect Compatible
# ═══════════════════════════════════════════════════════════════

class PrepareMintRequest(BaseModel):
    """Request to prepare an NFT for minting
    
    Compatible with Telegram Web App SDK form submissions
    """
    
    name: str = Field(..., min_length=1, max_length=255, description="NFT name")
    description: str = Field(..., min_length=1, max_length=2000, description="NFT description")
    image_url: str = Field(..., description="IPFS or HTTP URL to image")
    collection_address: Optional[str] = Field(None, description="Collection contract address")
    royalty_percent: int = Field(0, ge=0, le=100, description="Royalty percentage 0-100")
    attributes: Optional[list] = Field(None, description="NFT traits/attributes")


class PrepareMintResponse(BaseModel):
    """Response with TON Connect formatted transaction
    
    Frontend receives this and passes to TON Connect:
    tonconnect.sendTransaction(tonconnect_tx)
    """
    
    success: bool = True
    status: str = "ready"
    
    # TON Connect transaction format (signed by wallet)
    tonconnect_tx: Dict[str, Any] = Field(..., description="TON Connect formatted transaction")
    
    # Metadata for UI
    metadata_uri: str = Field(..., description="IPFS or backend URI to metadata")
    estimated_fee_ton: str = Field("0.05", description="Estimated transaction fee")
    
    # For logging/debugging
    nft_id: str = Field(..., description="NFT ID for callback")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "status": "ready",
                "tonconnect_tx": {
                    "messages": [{
                        "address": "EQA5...",
                        "amount": "50000000",
                        "payload": '{"type": "nft_mint", "owner": "EQAA..."}',
                    }],
                    "validUntil": 1234567890,
                    "network": "-239"
                },
                "metadata_uri": "https://api.example.com/nft/meta/123",
                "estimated_fee_ton": "0.05",
                "nft_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class ConfirmMintRequest(BaseModel):
    """Request to confirm minted NFT from TON Connect callback
    
    Frontend receives transaction_hash from TON Connect after user signs
    """
    
    transaction_hash: str = Field(..., description="Transaction hash from blockchain")
    nft_id: str = Field(..., description="NFT ID from prepare-mint response")
    wallet_address: Optional[str] = Field(None, description="Wallet that sent transaction")


class ConfirmMintResponse(BaseModel):
    """Response confirming mint success
    
    Frontend polls this endpoint until confirmations reach 101
    """
    
    success: bool = True
    status: str = Field(..., description="pending|in_progress|confirmed")
    nft_id: str = Field(..., description="NFT ID")
    
    # Confirmation tracking
    confirmations: int = Field(..., description="Block confirmations (0-120+)")
    trust_level: int = Field(..., ge=0, le=10, description="Trust score 0-10")
    
    # Optional: on-chain reference
    on_chain_address: Optional[str] = Field(None, description="On-chain NFT address when confirmed")


class VerifyTransactionRequest(BaseModel):
    """Request to verify a blockchain transaction"""
    
    transaction_hash: str = Field(..., description="Transaction hash")


class VerifyTransactionResponse(BaseModel):
    """Transaction verification status
    
    Called by frontend polling during transaction confirmation
    """
    
    success: bool = True
    found: bool = Field(..., description="Was transaction found on-chain")
    status: str = Field(..., description="pending|in_progress|confirmed|failed|not_found")
    confirmations: int = Field(..., description="Number of block confirmations")
    trust_level: int = Field(..., ge=0, le=10, description="Trust score 0-10")
    last_verified_at: Optional[str] = Field(None, description="ISO timestamp of verification")


class WalletSyncRequest(BaseModel):
    """Sync wallet connection state from frontend to backend
    
    Called by frontend after TON Connect connect/disconnect
    """
    
    wallet_address: str = Field(..., description="TON wallet address")
    wallet_name: str = Field(..., description="Wallet type (tonkeeper, mytonwallet, etc)")
    is_connected: bool = Field(..., description="True if connected, False if disconnected")


class WalletSyncResponse(BaseModel):
    """Confirmation of wallet sync"""
    
    success: bool = True
    wallet_address: str = Field(..., description="Synced wallet address")
    is_connected: bool = Field(..., description="Connection state")


class ErrorResponse(BaseModel):
    """Standard error response for Telegram SDK compatibility
    
    Frontend expects this format for all errors
    """
    
    success: bool = False
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post(
    "/nft/prepare-mint",
    response_model=PrepareMintResponse,
    summary="Prepare NFT for minting",
    description="Generate mint payload and metadata for blockchain submission via TON Connect",
)
async def prepare_nft_mint(
    request: PrepareMintRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Prepare an NFT for minting on TON blockchain
    
    Flow (Frontend):
    1. Call this endpoint with NFT metadata
    2. Receive TON Connect formatted transaction
    3. Call tonconnect.sendTransaction(response.tonconnect_tx)
    4. Wait for transaction hash from wallet
    5. Call confirm-mint endpoint with transaction hash
    
    Flow (Backend):
    1. Validate metadata
    2. Generate metadata JSON
    3. Upload to IPFS (or store on backend)
    4. Generate mint payload (BOC format)
    5. Format as TON Connect transaction
    6. Return ready for signing
    """
    
    try:
        nft_id = str(uuid.uuid4())
        logger.info(f"[PrepareMint] User {current_user.id} preparing mint: {request.name} (ID: {nft_id})")
        
        # 1. Generate metadata
        metadata = NFTMetadataService.generate_metadata(
            name=request.name,
            description=request.description,
            image_url=request.image_url,
            attributes=request.attributes,
        )
        
        # 2. Validate metadata
        is_valid, error = NFTMetadataService.validate_metadata(metadata)
        if not is_valid:
            logger.warning(f"[PrepareMint] Invalid metadata: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metadata: {error}"
            )
        
        # 3. Generate metadata JSON
        metadata_json = NFTMetadataService.generate_metadata_json(metadata)
        
        # For now, use backend-hosted metadata
        # In production: upload to IPFS and return IPFS hash
        metadata_uri = NFTMetadataService.generate_backend_metadata_uri(nft_id)
        
        # 4. Generate mint payload
        # Use user's wallet as owner (must be connected)
        owner_address = current_user.wallet_address
        if not owner_address:
            logger.warning(f"[PrepareMint] User {current_user.id} has no wallet connected")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wallet not connected. Please connect a TON wallet first."
            )
        
        backend_payload = NFTContractPayloads.encode_nft_mint_payload(
            owner_address=owner_address,
            content_uri=metadata_uri,
            royalty_address=request.collection_address or owner_address,
            royalty_percent=request.royalty_percent,
            metadata={"title": request.name, "description": request.description},
        )
        
        # 5. Format as TON Connect transaction
        collection_address = request.collection_address or owner_address
        tonconnect_tx = TONConnectTransaction.format_nft_mint_for_tonconnect(
            collection_address=collection_address,
            owner_address=owner_address,
            content_uri=metadata_uri,
            royalty_percent=request.royalty_percent,
            royalty_address=request.collection_address,
            amount_ton="0.05",
        )
        
        logger.info(f"[PrepareMint] Transaction ready for signing: {nft_id}")
        
        # 6. Return ready for wallet signing
        return PrepareMintResponse(
            success=True,
            status="ready",
            tonconnect_tx=tonconnect_tx,
            metadata_uri=metadata_uri,
            estimated_fee_ton="0.05",
            nft_id=nft_id,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PrepareMint] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prepare mint. Please try again."
        )


@router.post(
    "/nft/confirm-mint",
    response_model=ConfirmMintResponse,
    summary="Confirm minted NFT",
    description="Verify transaction on-chain and finalize NFT creation",
)
async def confirm_nft_mint(
    request: ConfirmMintRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Confirm that NFT was successfully minted on blockchain
    
    Telegram SDK & TON Connect Integration:
    1. Frontend waits for TON Connect callback (user signs transaction)
    2. Frontend receives transaction hash
    3. Frontend calls this endpoint with tx hash
    4. Backend stores transaction record
    5. Frontend polls this endpoint until confirmations >= 101
    
    Database:
    - Stores BlockchainTransaction record
    - Links to User and NFT records
    - Tracks confirmation count and trust level
    """
    
    try:
        logger.info(f"[ConfirmMint] User {current_user.id} confirming mint: {request.transaction_hash[:16]}...")
        
        # Validate transaction hash format
        if not all(c in '0123456789abcdefABCDEF' for c in request.transaction_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid transaction hash format"
            )
        
        # Validate wallet if provided
        if request.wallet_address and request.wallet_address != current_user.wallet_address:
            logger.warning(f"[ConfirmMint] Wallet mismatch for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Transaction wallet does not match connected wallet"
            )
        
        from sqlalchemy import select
        
        # Check if transaction already exists
        stmt = select(BlockchainTransaction).where(
            BlockchainTransaction.transaction_hash == request.transaction_hash
        )
        result = await db.execute(stmt)
        existing_tx = result.scalar_one_or_none()
        
        if existing_tx:
            logger.info(f"[ConfirmMint] Transaction already stored: {request.transaction_hash[:16]}...")
            return ConfirmMintResponse(
                success=True,
                status="pending" if existing_tx.confirmations < 51 else "in_progress" if existing_tx.confirmations < 101 else "confirmed",
                nft_id=request.nft_id,
                confirmations=existing_tx.confirmations,
                trust_level=existing_tx.trust_level,
            )
        
        # Store new transaction record - initially pending
        # Real TonCenter integration will update this via background job
        tx = BlockchainTransaction(
            user_id=current_user.id,
            wallet_address=request.wallet_address or current_user.wallet_address,
            transaction_hash=request.transaction_hash,
            transaction_type="mint",
            from_address=current_user.wallet_address,
            to_address=None,  # Will be determined by verification
            amount_nano_ton="50000000",
            status=BlockchainTransactionStatus.PENDING,
            confirmations=0,  # Starts at 0, background job will update
            trust_level=0,
            verification_attempts=0,
        )
        
        db.add(tx)
        await db.commit()
        await db.refresh(tx)
        
        logger.info(f"[ConfirmMint] Transaction stored: {request.transaction_hash[:16]}... (confirmations will be updated by background job)")
        
        return ConfirmMintResponse(
            success=True,
            status="pending",
            nft_id=request.nft_id,
            confirmations=0,
            trust_level=0,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ConfirmMint] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm mint. Please try again."
        )


@router.post(
    "/transaction/{tx_hash}/verify",
    response_model=VerifyTransactionResponse,
    summary="Verify blockchain transaction",
    description="Check transaction status on-chain and update confirmation count - Called by frontend polling",
)
async def verify_transaction(
    tx_hash: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Verify a transaction on TON blockchain (for polling)
    
    Frontend polls this endpoint to monitor transaction progress:
    - pending (0-50 confirmations)
    - in_progress (51-100 confirmations)
    - confirmed (101+ confirmations)
    
    Backend queries TonCenter (or background job updates DB)
    """
    
    try:
        from sqlalchemy import select
        
        logger.info(f"[VerifyTransaction] User {current_user.id} polling: {tx_hash[:16]}...")
        
        # Find transaction in database
        stmt = select(BlockchainTransaction).where(
            BlockchainTransaction.transaction_hash == tx_hash
        )
        result = await db.execute(stmt)
        tx = result.scalar_one_or_none()
        
        if not tx:
            logger.warning(f"[VerifyTransaction] Transaction not found: {tx_hash[:16]}...")
            return VerifyTransactionResponse(
                success=True,
                found=False,
                status="not_found",
                confirmations=0,
                trust_level=0,
            )
        
        # Verify transaction belongs to user
        if tx.user_id != current_user.id:
            logger.warning(f"[VerifyTransaction] Access denied for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to verify this transaction"
            )
        
        # Determine status from confirmations
        if tx.confirmations >= 101:
            tx_status = "confirmed"
        elif tx.confirmations >= 51:
            tx_status = "in_progress"
        elif tx.confirmations > 0:
            tx_status = "pending"
        elif tx.status == BlockchainTransactionStatus.FAILED:
            tx_status = "failed"
        else:
            tx_status = "pending"
        
        from datetime import datetime
        last_verified_at = tx.verification_attempts_at.isoformat() if hasattr(tx, 'verification_attempts_at') else datetime.utcnow().isoformat()
        
        logger.info(f"[VerifyTransaction] {tx_hash[:16]}... status: {tx_status} ({tx.confirmations} confirmations)")
        
        return VerifyTransactionResponse(
            success=True,
            found=True,
            status=tx_status,
            confirmations=tx.confirmations,
            trust_level=tx.trust_level,
            last_verified_at=last_verified_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VerifyTransaction] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify transaction"
        )


# ═══════════════════════════════════════════════════════════════
# WALLET INTEGRATION ENDPOINTS (TON Connect)
# ═══════════════════════════════════════════════════════════════


@router.post(
    "/wallet/sync",
    response_model=WalletSyncResponse,
    summary="Sync wallet connection state",
    description="Synchronize TON Connect wallet state from frontend to backend",
)
async def sync_wallet_connection(
    request: WalletSyncRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Sync wallet connection from TON Connect UI to backend
    
    Called after:
    1. User connects wallet in TON Connect
    2. User disconnects wallet
    
    Enables backend to track:
    - Which wallet is connected
    - When connection happened
    - Wallet type (Tonkeeper, MyTonWallet, etc)
    
    Telegram SDK Integration:
    - Uses X-Telegram-Init-Data header for auth
    - Updates backend wallet state
    - Returns confirmation
    """
    
    try:
        logger.info(f"[WalletSync] User {current_user.id} syncing wallet: {request.wallet_address[:10]}... (connected={request.is_connected})")
        
        # Validate TON address format (basic)
        if not request.wallet_address.startswith("EQ") and not request.wallet_address.startswith("UQ"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TON wallet address format"
            )
        
        # Sync wallet to backend
        wallet = await TONConnectWalletSync.sync_wallet_connection(
            user=current_user,
            wallet_address=request.wallet_address,
            wallet_name=request.wallet_name,
            is_connected=request.is_connected,
            db_session=db,
        )
        
        if request.is_connected and wallet:
            logger.info(f"[WalletSync] Wallet connected: {request.wallet_address[:10]}...")
        elif not request.is_connected:
            logger.info(f"[WalletSync] Wallet disconnected: {request.wallet_address[:10]}...")
        
        return WalletSyncResponse(
            success=True,
            wallet_address=request.wallet_address,
            is_connected=request.is_connected,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WalletSync] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync wallet"
        )
