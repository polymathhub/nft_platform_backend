"""
Wallet Persistence & Status Router
Handles persistent wallet connections, status checking, and balance queries

Required for real Web3 - wallet connection should survive page reloads and browser restarts
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.database import get_db_session
from app.models import User, TONWallet
from app.models.ton_wallet import TONWalletStatus
from app.utils.telegram_auth_dependency import get_current_user
from app.config import get_settings
from app.services.ton_blockchain_service import TONBlockchainService
from decimal import Decimal

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/wallets", tags=["wallet-persistence"])


# ═══════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════

class WalletStatusResponse(BaseModel):
    """Wallet connection status"""
    id: str
    address: str
    status: str  # pending, connected, disconnected, failed
    is_primary: bool
    is_connected: bool  # True if status == "connected"
    connected_at: Optional[datetime] = None
    balance_ton: Optional[float] = None
    wallet_name: Optional[str] = None
    device_info: Optional[str] = None
    last_activity: Optional[datetime] = None


class UserWalletsResponse(BaseModel):
    """List of user's connected wallets"""
    total: int
    wallets: List[WalletStatusResponse]
    primary_wallet: Optional[WalletStatusResponse] = None


class CurrentWalletResponse(BaseModel):
    """Current/primary wallet info"""
    connected: bool
    wallet: Optional[WalletStatusResponse] = None
    message: str


class WalletBalanceResponse(BaseModel):
    """Wallet balance and status"""
    address: str
    balance_ton: float
    balance_nanoton: int
    is_connected: bool
    connected_at: Optional[datetime] = None
    last_checked: datetime


class SetPrimaryWalletRequest(BaseModel):
    """Set wallet as primary"""
    wallet_id: str


class SetPrimaryWalletResponse(BaseModel):
    """Response when setting primary wallet"""
    success: bool
    primary_wallet: WalletStatusResponse


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _ton_wallet_to_response(wallet: TONWallet, balance: Optional[Decimal] = None) -> WalletStatusResponse:
    """Convert TONWallet model to response"""
    is_connected = wallet.status == TONWalletStatus.CONNECTED
    
    metadata = wallet.wallet_metadata or {}
    
    return WalletStatusResponse(
        id=str(wallet.id),
        address=wallet.wallet_address,
        status=wallet.status.value,
        is_primary=wallet.is_primary,
        is_connected=is_connected,
        connected_at=wallet.connected_at,
        balance_ton=float(balance) if balance else None,
        wallet_name=metadata.get("wallet_name"),
        device_info=metadata.get("device"),
        last_activity=metadata.get("last_activity"),
    )


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/current", response_model=CurrentWalletResponse)
async def get_current_wallet(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> CurrentWalletResponse:
    """
    Get user's current/primary connected wallet
    
    Returns status and balance if connected
    """
    try:
        # Find primary connected wallet
        result = await db.execute(
            select(TONWallet).where(
                and_(
                    TONWallet.user_id == current_user.id,
                    TONWallet.is_primary == True,
                    TONWallet.status == TONWalletStatus.CONNECTED
                )
            )
        )
        wallet = result.scalar_one_or_none()
        
        if wallet:
            # Get balance
            balance, _ = await TONBlockchainService.get_wallet_balance(wallet.wallet_address)
            wallet_response = _ton_wallet_to_response(wallet, balance)
            
            return CurrentWalletResponse(
                connected=True,
                wallet=wallet_response,
                message=f"Connected to {wallet.wallet_address[:10]}..."
            )
        else:
            return CurrentWalletResponse(
                connected=False,
                wallet=None,
                message="No wallet connected. Please connect a wallet in the Wallet tab."
            )
    
    except Exception as e:
        logger.error(f"[Wallet] Error getting current wallet: {e}")
        return CurrentWalletResponse(
            connected=False,
            wallet=None,
            message="Error checking wallet status"
        )


@router.get("/status", response_model=CurrentWalletResponse)
async def check_wallet_status(
    address: Optional[str] = Query(None, description="Specific wallet address to check"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> CurrentWalletResponse:
    """
    Check if user has a connected wallet
    
    If address provided, check that specific wallet
    Otherwise return primary connected wallet status
    """
    try:
        if address:
            # Check specific wallet
            result = await db.execute(
                select(TONWallet).where(
                    and_(
                        TONWallet.user_id == current_user.id,
                        TONWallet.wallet_address == address
                    )
                )
            )
            wallet = result.scalar_one_or_none()
            
            if not wallet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Wallet not found for this user"
                )
        else:
            # Get primary wallet
            result = await db.execute(
                select(TONWallet).where(
                    and_(
                        TONWallet.user_id == current_user.id,
                        TONWallet.is_primary == True
                    )
                )
            )
            wallet = result.scalar_one_or_none()
        
        if not wallet:
            return CurrentWalletResponse(
                connected=False,
                wallet=None,
                message="No wallet connected"
            )
        
        is_connected = wallet.status == TONWalletStatus.CONNECTED
        
        # Get balance if connected
        balance = None
        if is_connected:
            balance, _ = await TONBlockchainService.get_wallet_balance(wallet.wallet_address)
        
        wallet_response = _ton_wallet_to_response(wallet, balance)
        
        return CurrentWalletResponse(
            connected=is_connected,
            wallet=wallet_response,
            message="Wallet connected" if is_connected else "Wallet disconnected"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Wallet] Error checking status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check wallet status"
        )


@router.get("/primary", response_model=CurrentWalletResponse)
async def get_primary_wallet(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> CurrentWalletResponse:
    """
    Get user's primary wallet (alias for /current)
    """
    return await get_current_wallet(db, current_user)


@router.get("", response_model=UserWalletsResponse)
async def list_user_wallets(
    status_filter: Optional[str] = Query(None, description="Filter by status: connected, disconnected, pending"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserWalletsResponse:
    """
    List all wallets connected by user
    
    Returns list with balances for connected wallets
    """
    try:
        # Build query
        query = select(TONWallet).where(TONWallet.user_id == current_user.id)
        
        if status_filter:
            query = query.where(TONWallet.status == status_filter)
        
        query = query.order_by(desc(TONWallet.is_primary), desc(TONWallet.connected_at))
        
        result = await db.execute(query)
        wallets = result.scalars().all()
        
        # Get balances for connected wallets
        wallet_responses = []
        primary_wallet = None
        
        for wallet in wallets:
            balance = None
            if wallet.status == TONWalletStatus.CONNECTED:
                balance, _ = await TONBlockchainService.get_wallet_balance(wallet.wallet_address)
            
            response = _ton_wallet_to_response(wallet, balance)
            wallet_responses.append(response)
            
            if wallet.is_primary and wallet.status == TONWalletStatus.CONNECTED:
                primary_wallet = response
        
        return UserWalletsResponse(
            total=len(wallets),
            wallets=wallet_responses,
            primary_wallet=primary_wallet
        )
    
    except Exception as e:
        logger.error(f"[Wallet] Error listing wallets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list wallets"
        )


@router.get("/balance/{address}", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    address: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> WalletBalanceResponse:
    """
    Get balance of a connected wallet
    
    Only works for wallets owned by the user
    """
    try:
        # Verify user owns this wallet
        result = await db.execute(
            select(TONWallet).where(
                and_(
                    TONWallet.user_id == current_user.id,
                    TONWallet.wallet_address == address
                )
            )
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wallet not found or not connected to your account"
            )
        
        # Get balance from blockchain
        balance_ton, error = await TONBlockchainService.get_wallet_balance(address)
        
        if error:
            logger.warning(f"[Wallet] Balance query error for {address}: {error}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cannot query blockchain: {error}"
            )
        
        if balance_ton is None:
            balance_ton = Decimal("0")
        
        balance_nanoton = int(balance_ton * Decimal(10) ** Decimal(9))
        
        return WalletBalanceResponse(
            address=address,
            balance_ton=float(balance_ton),
            balance_nanoton=balance_nanoton,
            is_connected=wallet.status == TONWalletStatus.CONNECTED,
            connected_at=wallet.connected_at,
            last_checked=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Wallet] Error getting balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get wallet balance"
        )


@router.post("/primary", response_model=SetPrimaryWalletResponse)
async def set_primary_wallet(
    request: SetPrimaryWalletRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> SetPrimaryWalletResponse:
    """
    Set a connected wallet as primary wallet
    
    Primary wallet is used for minting and marketplace operations
    """
    try:
        wallet_id = UUID(request.wallet_id)
        
        # Verify user owns this wallet
        result = await db.execute(
            select(TONWallet).where(
                and_(
                    TONWallet.user_id == current_user.id,
                    TONWallet.id == wallet_id
                )
            )
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found"
            )
        
        if wallet.status != TONWalletStatus.CONNECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wallet must be connected to set as primary"
            )
        
        # Set all other wallets as non-primary
        await db.execute(
            select(TONWallet)
            .where(TONWallet.user_id == current_user.id)
            .update({"is_primary": False})
        )
        
        # Set this wallet as primary
        wallet.is_primary = True
        await db.commit()
        
        logger.info(f"[Wallet] User {current_user.id} set wallet {wallet.wallet_address} as primary")
        
        # Get balance
        balance, _ = await TONBlockchainService.get_wallet_balance(wallet.wallet_address)
        
        return SetPrimaryWalletResponse(
            success=True,
            primary_wallet=_ton_wallet_to_response(wallet, balance)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Wallet] Error setting primary wallet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set primary wallet"
        )


@router.post("/refresh-status/{address}")
async def refresh_wallet_status(
    address: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> WalletStatusResponse:
    """
    Refresh wallet status and balance
    
    Useful after wallet operations to update balance
    """
    try:
        # Verify user owns this wallet
        result = await db.execute(
            select(TONWallet).where(
                and_(
                    TONWallet.user_id == current_user.id,
                    TONWallet.wallet_address == address
                )
            )
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wallet not found or not connected to your account"
            )
        
        # Update last activity
        wallet.wallet_metadata = {
            **(wallet.wallet_metadata or {}),
            "last_activity": datetime.utcnow().isoformat()
        }
        await db.commit()
        
        # Get fresh balance
        balance, _ = await TONBlockchainService.get_wallet_balance(address)
        
        logger.info(f"[Wallet] Refreshed status for {address}")
        
        return _ton_wallet_to_response(wallet, balance)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Wallet] Error refreshing status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh wallet status"
        )
