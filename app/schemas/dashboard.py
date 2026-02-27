"""
Dashboard and Statistics Response Schemas
"""

from pydantic import BaseModel
from typing import List, Optional


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics aggregation"""
    nfts_owned: int
    active_listings: int
    total_balance: float
    profit_24h: float
    wallet_balance: float
    total_profit: float

    class Config:
        from_attributes = True


class WalletBalanceResponse(BaseModel):
    """Current wallet balance and token info"""
    balance: float
    currency: str = "USD"
    token_balance: float
    token_symbol: str
    total_profit: float

    class Config:
        from_attributes = True


class NFTItem(BaseModel):
    """Individual NFT in collection"""
    id: str
    name: str
    owner: str
    price: float
    image: str

    class Config:
        from_attributes = True


class UserNFTsResponse(BaseModel):
    """User's NFT collection"""
    nfts: List[NFTItem]
    total: int

    class Config:
        from_attributes = True


class TransactionItem(BaseModel):
    """Individual transaction"""
    id: str
    icon: str
    title: str
    description: str
    type: str  # "positive", "negative", "neutral"
    amount: str

    class Config:
        from_attributes = True


class RecentTransactionsResponse(BaseModel):
    """Recent transactions list"""
    transactions: List[TransactionItem]

    class Config:
        from_attributes = True
