from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from enum import Enum

class BlockchainEnum(str, Enum):
    TON = "ton"
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    BITCOIN = "bitcoin"
    AVALANCHE = "avalanche"
    
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"


class WalletTypeEnum(str, Enum):
    CUSTODIAL = "custodial"
    SELF_CUSTODY = "self_custody"


class CreateWalletRequest(BaseModel):
    blockchain: BlockchainEnum
    wallet_type: WalletTypeEnum = WalletTypeEnum.CUSTODIAL
    is_primary: bool = False


class ImportWalletRequest(BaseModel):
    blockchain: BlockchainEnum
    address: str
    wallet_type: WalletTypeEnum = WalletTypeEnum.SELF_CUSTODY
    public_key: Optional[str] = None
    is_primary: bool = False


class WalletResponse(BaseModel):
    id: UUID
    blockchain: BlockchainEnum
    wallet_type: WalletTypeEnum
    address: str
    public_key: Optional[str]
    is_primary: bool
    is_active: bool
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WalletDetailResponse(WalletResponse):
    user_id: UUID


class SetPrimaryWalletRequest(BaseModel):
    wallet_id: UUID


class WalletBalanceResponse(BaseModel):
    address: str
    blockchain: BlockchainEnum
    balance: str
    symbol: str
    decimals: int


class WalletTransactionHistoryResponse(BaseModel):
    address: str
    blockchain: BlockchainEnum
    transactions: list
