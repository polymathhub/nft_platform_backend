from pydantic import BaseModel
from typing import List, Optional
class DashboardStatsResponse(BaseModel):
    nfts_owned: int
    active_listings: int
    total_balance: float
    profit_24h: float
    wallet_balance: float
    total_profit: float
    class Config:
        from_attributes = True
class WalletBalanceResponse(BaseModel):
    balance: float
    currency: str = "USD"
    token_balance: float
    token_symbol: str
    total_profit: float
    class Config:
        from_attributes = True
class NFTItem(BaseModel):
    id: str
    name: str
    owner: str
    price: float
    image: str
    class Config:
        from_attributes = True
class UserNFTsResponse(BaseModel):
    nfts: List[NFTItem]
    total: int
    class Config:
        from_attributes = True
class TransactionItem(BaseModel):
    id: str
    icon: str
    title: str
    description: str
    type: str
    amount: str
    class Config:
        from_attributes = True
class RecentTransactionsResponse(BaseModel):
    transactions: List[TransactionItem]
    class Config:
        from_attributes = True
