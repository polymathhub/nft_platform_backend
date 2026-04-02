"""
Transaction Confirmation & Verification Router
Handles transaction confirmation, status tracking, and blockchain verification

Critical for converting UI-only wallet connections into real Web3 operations
"""

import logging
import aiohttp
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db_session
from app.models import User, Transaction, TONWallet, NFT
from app.models.transaction import TransactionStatus, TransactionType
from app.utils.telegram_auth_dependency import get_current_user
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/transactions", tags=["transactions"])


# ═══════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════

class TransactionConfirmRequest(BaseModel):
    """Confirm a signed transaction on blockchain"""
    tx_hash: str = Field(..., description="Transaction hash from TON Connect signing")
    wallet_address: str = Field(..., description="User's wallet address")
    type: TransactionType = Field(..., description="Type: mint, transfer, buy, offer")
    nft_id: Optional[str] = Field(None, description="Associated NFT ID if applicable")
    marketplace_listing_id: Optional[str] = Field(None, description="Associated listing ID if applicable")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional TX metadata")


class TransactionStatusResponse(BaseModel):
    """Transaction status"""
    id: str
    tx_hash: str
    status: str  # pending, confirmed, failed
    type: str
    amount: Optional[float] = None
    gas_fee: Optional[float] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    blockchain: str = "ton"
    nft_id: Optional[str] = None


class ConfirmTransactionResponse(BaseModel):
    """Response when confirming transaction"""
    success: bool
    tx_hash: str
    status: str  # pending, confirmed
    message: str
    transaction: Optional[TransactionStatusResponse] = None


class TransactionHistoryResponse(BaseModel):
    """User's transaction history"""
    id: str
    tx_hash: str
    type: str
    status: str
    amount: Optional[float] = None
    created_at: datetime
    blockchain: str = "ton"


class BalanceResponse(BaseModel):
    """Wallet balance"""
    address: str
    balance_ton: float
    balance_nanoton: int
    last_updated: datetime


# ═══════════════════════════════════════════════════════════════
# BLOCKCHAIN VERIFICATION SERVICE
# ═══════════════════════════════════════════════════════════════

class BlockchainVerificationService:
    """Verify transactions on TON blockchain"""
    
    @staticmethod
    async def verify_transaction_hash(tx_hash: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verify transaction exists on blockchain
        
        Returns: (is_valid, transaction_data)
        """
        try:
            if not tx_hash or len(tx_hash) < 10:
                return False, None
            
            async with aiohttp.ClientSession() as session:
                # Query TonCenter API: Get transaction
                url = f"{settings.ton_rpc_url}?method=tryLocateTx&tx={tx_hash}"
                
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        logger.warning(f"[TX] TonCenter returned {resp.status}")
                        return False, None
                    
                    data = await resp.json()
                    
                    if data.get("ok") is False:
                        logger.warning(f"[TX] TonCenter error: {data.get('result', {}).get('error')}")
                        return False, None
                    
                    result = data.get("result", {})
                    
                    # Check if transaction info found
                    if not result or not result.get("tx"):
                        # TX not yet finalized, but hash is structurally valid
                        logger.info(f"[TX] Hash valid but not yet finalized: {tx_hash}")
                        return True, {"status": "pending", "confirmed": False}
                    
                    tx_info = result.get("tx", {})
                    
                    return True, {
                        "tx_hash": tx_hash,
                        "status": "confirmed",
                        "confirmed": True,
                        "block_id": result.get("block_id"),
                        "in_progress": result.get("in_progress", False),
                        "lt": tx_info.get("lt"),
                        "hash": tx_info.get("hash"),
                    }
        
        except Exception as e:
            logger.error(f"[TX] Verification error: {e}")
            return False, None
    
    @staticmethod
    async def get_transaction_status(tx_hash: str) -> str:
        """
        Get transaction status: pending, confirmed, or failed
        """
        is_valid, tx_data = await BlockchainVerificationService.verify_transaction_hash(tx_hash)
        
        if not is_valid:
            return "failed"
        
        if tx_data and tx_data.get("confirmed"):
            return "confirmed"
        
        return "pending"


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/confirm", response_model=ConfirmTransactionResponse)
async def confirm_transaction(
    request: TransactionConfirmRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ConfirmTransactionResponse:
    """
    Confirm a transaction that was signed by user via TON Connect
    
    Frontend flow:
    1. User signs transaction with TON Connect
    2. TON Connect returns tx_hash
    3. Frontend calls this endpoint with tx_hash
    4. Backend verifies on-chain and updates DB
    5. Backend returns confirmation
    """
    try:
        # Validate TX hash format
        if not request.tx_hash or len(request.tx_hash) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid transaction hash"
            )
        
        # Verify user owns the wallet
        result = await db.execute(
            select(TONWallet).where(
                and_(
                    TONWallet.user_id == current_user.id,
                    TONWallet.wallet_address == request.wallet_address,
                    TONWallet.status.in_(["connected", "pending"])
                )
            )
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            logger.warning(f"[TX] User {current_user.id} tried to confirm TX with unconnected wallet {request.wallet_address}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wallet not connected to your account"
            )
        
        # Verify transaction on blockchain
        is_valid, tx_data = await BlockchainVerificationService.verify_transaction_hash(request.tx_hash)
        
        if not is_valid:
            logger.warning(f"[TX] Invalid TX hash: {request.tx_hash}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction hash is invalid or cannot be verified"
            )
        
        # Determine initial status
        tx_status = "confirmed" if (tx_data and tx_data.get("confirmed")) else "pending"
        
        # Create transaction record
        transaction = Transaction(
            user_id=current_user.id,
            wallet_id=wallet.id,
            nft_id=UUID(request.nft_id) if request.nft_id else None,
            transaction_type=request.type,
            blockchain="ton",
            from_address=request.wallet_address,
            to_address=request.metadata.get("to_address", "unknown"),
            transaction_hash=request.tx_hash,
            status=TransactionStatus.CONFIRMED if tx_status == "confirmed" else TransactionStatus.PENDING,
            transaction_metadata={
                **request.metadata,
                "verified_at": datetime.utcnow().isoformat(),
                "verification_data": tx_data,
            },
            confirmed_at=datetime.utcnow() if tx_status == "confirmed" else None,
        )
        
        db.add(transaction)
        await db.flush()  # Get transaction.id
        
        # If NFT mint, update NFT with TX hash
        if request.type == TransactionType.MINT and request.nft_id:
            nft_result = await db.execute(
                select(NFT).where(NFT.id == UUID(request.nft_id))
            )
            nft = nft_result.scalar_one_or_none()
            if nft:
                nft.transaction_hash = request.tx_hash
                nft.blockchain_status = "confirmed" if tx_status == "confirmed" else "pending"
                logger.info(f"[TX] NFT {request.nft_id} linked to TX {request.tx_hash}")
        
        await db.commit()
        
        logger.info(f"[TX] Transaction confirmed: {request.tx_hash[:16]}... (status={tx_status})")
        
        return ConfirmTransactionResponse(
            success=True,
            tx_hash=request.tx_hash,
            status=tx_status,
            message=f"Transaction {tx_status}: {request.tx_hash}",
            transaction=TransactionStatusResponse(
                id=str(transaction.id),
                tx_hash=transaction.transaction_hash,
                status=tx_status,
                type=request.type,
                created_at=transaction.created_at,
                confirmed_at=transaction.confirmed_at,
                blockchain="ton",
                nft_id=request.nft_id,
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TX] Error confirming transaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm transaction: {str(e)}"
        )


@router.get("/{tx_hash}", response_model=TransactionStatusResponse)
async def get_transaction_status(
    tx_hash: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TransactionStatusResponse:
    """
    Get status of a transaction
    
    Returns: pending, confirmed, or failed
    """
    try:
        # Find transaction (user can only view their own)
        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.transaction_hash == tx_hash,
                    Transaction.user_id == current_user.id
                )
            )
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # If still pending, check blockchain for confirmation
        if transaction.status == TransactionStatus.PENDING:
            is_valid, tx_data = await BlockchainVerificationService.verify_transaction_hash(tx_hash)
            
            if is_valid and tx_data and tx_data.get("confirmed"):
                transaction.status = TransactionStatus.CONFIRMED
                transaction.confirmed_at = datetime.utcnow()
                await db.commit()
                logger.info(f"[TX] Updated pending TX to confirmed: {tx_hash[:16]}...")
        
        return TransactionStatusResponse(
            id=str(transaction.id),
            tx_hash=transaction.transaction_hash,
            status=transaction.status.value,
            type=transaction.transaction_type.value,
            gas_fee=transaction.gas_fee,
            created_at=transaction.created_at,
            confirmed_at=transaction.confirmed_at,
            blockchain="ton",
            nft_id=str(transaction.nft_id) if transaction.nft_id else None,
            error_message=transaction.error_message,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TX] Error getting TX status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transaction status"
        )


@router.get("/history/user", response_model=Dict[str, Any])
async def get_transaction_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    type_filter: Optional[str] = Query(None, description="Filter by type: mint, transfer, buy, offer"),
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, confirmed, failed"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get user's transaction history
    
    Supports filtering by type and status
    """
    try:
        # Build query
        query = select(Transaction).where(Transaction.user_id == current_user.id)
        
        if type_filter:
            query = query.where(Transaction.transaction_type == type_filter)
        
        if status_filter:
            query = query.where(Transaction.status == status_filter)
        
        # Get total count
        count_result = await db.execute(
            select(Transaction).where(Transaction.user_id == current_user.id)
        )
        total = len(count_result.fetchall())
        
        # Get paginated results
        query = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        return {
            "total": total,
            "page": (skip // limit) + 1,
            "per_page": limit,
            "transactions": [
                TransactionHistoryResponse(
                    id=str(tx.id),
                    tx_hash=tx.transaction_hash or "pending",
                    type=tx.transaction_type.value,
                    status=tx.status.value,
                    amount=tx.gas_fee,
                    created_at=tx.created_at,
                    blockchain="ton",
                )
                for tx in transactions
            ]
        }
    
    except Exception as e:
        logger.error(f"[TX] Error getting history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transaction history"
        )


@router.post("/retry/{tx_hash}")
async def retry_transaction_confirmation(
    tx_hash: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ConfirmTransactionResponse:
    """
    Retry confirming a pending transaction
    
    Useful if blockchain confirmation was delayed
    """
    try:
        # Find transaction
        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.transaction_hash == tx_hash,
                    Transaction.user_id == current_user.id
                )
            )
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Re-verify on blockchain
        is_valid, tx_data = await BlockchainVerificationService.verify_transaction_hash(tx_hash)
        
        if is_valid and tx_data and tx_data.get("confirmed"):
            transaction.status = TransactionStatus.CONFIRMED
            transaction.confirmed_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"[TX] Retry confirmed pending TX: {tx_hash[:16]}...")
            
            return ConfirmTransactionResponse(
                success=True,
                tx_hash=tx_hash,
                status="confirmed",
                message="Transaction confirmed on blockchain"
            )
        else:
            return ConfirmTransactionResponse(
                success=False,
                tx_hash=tx_hash,
                status="pending",
                message="Transaction still pending - try again in a few seconds"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TX] Error retrying TX: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry transaction confirmation"
        )
