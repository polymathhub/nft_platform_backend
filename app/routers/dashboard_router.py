"""
Dashboard and Statistics Routes
Provides aggregated data for the main dashboard view
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
import logging
from datetime import datetime, timedelta

from app.database import get_db_session
from app.models import User, NFT, Wallet, Payment, Transaction
from app.security.auth import get_current_user
from app.schemas.dashboard import (
    DashboardStatsResponse,
    WalletBalanceResponse,
    UserNFTsResponse,
    RecentTransactionsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# ==================== STATS ENDPOINT ====================
@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get aggregated dashboard statistics:
    - NFTs owned count
    - Active listings count
    - Total portfolio value
    - 24h profit/loss
    """
    try:
        # Count NFTs owned by user
        nft_count_result = await db.execute(
            select(func.count(NFT.id)).where(NFT.owner_id == current_user.id)
        )
        nfts_owned = nft_count_result.scalar() or 0

        # Count active listings by user
        active_listings_result = await db.execute(
            select(func.count(NFT.id)).where(
                (NFT.owner_id == current_user.id) & (NFT.is_listed == True)
            )
        )
        active_listings = active_listings_result.scalar() or 0

        # Calculate total portfolio value (from wallets)
        wallets_result = await db.execute(
            select(Wallet).where(Wallet.user_id == current_user.id)
        )
        wallets = wallets_result.scalars().all()
        
        total_balance = sum(float(w.balance or 0) for w in wallets)
        
        # Get profit from last 24 hours
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        transactions_result = await db.execute(
            select(func.sum(Transaction.amount)).where(
                (Transaction.user_id == current_user.id) &
                (Transaction.created_at >= twenty_four_hours_ago) &
                (Transaction.transaction_type == "PROFIT")
            )
        )
        profit_24h = float(transactions_result.scalar() or 0)

        return DashboardStatsResponse(
            nfts_owned=nfts_owned,
            active_listings=active_listings,
            total_balance=total_balance,
            profit_24h=profit_24h,
            wallet_balance=max(w.balance for w in wallets) if wallets else 0,
            total_profit=profit_24h,
        )

    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard statistics",
        )


# ==================== WALLET BALANCE ENDPOINT ====================
@router.get("/wallet/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get primary wallet balance and token information
    """
    try:
        # Get primary wallet
        wallet_result = await db.execute(
            select(Wallet).where(
                (Wallet.user_id == current_user.id) & (Wallet.is_primary == True)
            )
        )
        primary_wallet = wallet_result.scalar_one_or_none()

        if not primary_wallet:
            # Return default if no primary wallet
            return WalletBalanceResponse(
                balance=0,
                currency="USD",
                token_balance=0,
                token_symbol="ETH",
                total_profit=0,
            )

        return WalletBalanceResponse(
            balance=float(primary_wallet.balance or 0),
            currency="USD",
            token_balance=float(primary_wallet.balance or 0) / 100,  # Mock conversion
            token_symbol=primary_wallet.blockchain.name,
            total_profit=450.00,  # TODO: Calculate from transaction history
        )

    except Exception as e:
        logger.error(f"Error getting wallet balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch wallet balance",
        )


# ==================== USER NFTs ENDPOINT ====================
@router.get("/nfts", response_model=UserNFTsResponse)
async def get_user_nfts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = 10,
    offset: int = 0,
):
    """
    Get NFTs owned by current user with pagination
    """
    try:
        # Get total count
        count_result = await db.execute(
            select(func.count(NFT.id)).where(NFT.owner_id == current_user.id)
        )
        total = count_result.scalar() or 0

        # Get paginated NFTs
        nfts_result = await db.execute(
            select(NFT)
            .where(NFT.owner_id == current_user.id)
            .order_by(NFT.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        nfts = nfts_result.scalars().all()

        nft_data = [
            {
                "id": str(nft.id),
                "name": nft.name or "Unnamed NFT",
                "owner": current_user.username or "Owner",
                "price": float(nft.price or 0),
                "image": nft.image_url or f"data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Crect fill=%226B5B95%22 width=%22200%22 height=%22200%22/%3E%3C/svg%3E",
            }
            for nft in nfts
        ]

        return UserNFTsResponse(nfts=nft_data, total=total)

    except Exception as e:
        logger.error(f"Error getting user NFTs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user NFTs",
        )


# ==================== RECENT TRANSACTIONS ENDPOINT ====================
@router.get("/transactions/recent", response_model=RecentTransactionsResponse)
async def get_recent_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = 10,
):
    """
    Get the most recent transactions for the user
    """
    try:
        transactions_result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == current_user.id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        transactions = transactions_result.scalars().all()

        transaction_data = [
            {
                "id": str(tx.id),
                "icon": "📊" if tx.transaction_type == "SALE" else "💰",
                "title": f"Transaction #{tx.id}",
                "description": f"{(datetime.utcnow() - tx.created_at).days} days ago",
                "type": "positive" if tx.transaction_type in ["PROFIT", "RECEIVED"] else "negative",
                "amount": f"${abs(float(tx.amount or 0)):.2f}",
            }
            for tx in transactions
        ]

        return RecentTransactionsResponse(transactions=transaction_data)

    except Exception as e:
        logger.error(f"Error getting recent transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transactions",
        )
