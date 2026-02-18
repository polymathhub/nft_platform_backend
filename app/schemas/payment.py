from pydantic import BaseModel, Field, validator
from typing import Optional
from uuid import UUID


class InitiateDepositRequest(BaseModel):
    """Request to initiate a deposit."""
    wallet_id: UUID = Field(..., description="Target wallet to deposit into")
    amount: float = Field(..., ge=1, le=1000000, description="Amount to deposit in USDT")
    external_address: Optional[str] = Field(None, description="External wallet address sending funds (for reference)")


class DepositConfirmRequest(BaseModel):
    """Request to confirm a deposit via tx hash."""
    payment_id: UUID = Field(..., description="Payment record ID")
    transaction_hash: str = Field(..., min_length=10, description="External transaction hash")


class InitiateWithdrawalRequest(BaseModel):
    """Request to initiate a withdrawal."""
    wallet_id: UUID = Field(..., description="Source wallet to withdraw from")
    amount: float = Field(..., ge=1, le=1000000, description="Amount to withdraw in USDT")
    destination_address: str = Field(..., min_length=20, description="Destination wallet address")
    destination_blockchain: Optional[str] = Field(None, description="Target blockchain (if different)")


class WithdrawalApprovalRequest(BaseModel):
    """Request to approve a pending withdrawal."""
    payment_id: UUID = Field(..., description="Payment record ID")


class PaymentResponse(BaseModel):
    """Payment information response."""
    id: UUID
    payment_type: str
    status: str
    amount: float
    currency: str
    blockchain: str
    counterparty_address: Optional[str]
    transaction_hash: Optional[str]
    network_fee: Optional[float]
    platform_fee: Optional[float]
    created_at: str
    confirmed_at: Optional[str]

    class Config:
        from_attributes = True


class DepositInfoResponse(BaseModel):
    """Deposit information for user."""
    payment_id: UUID
    deposit_address: str  # Platform address to send to
    amount: float
    currency: str
    blockchain: str
    status: str
    instructions: str
    expires_in_hours: int = 24


class WithdrawalInfoResponse(BaseModel):
    """Withdrawal information."""
    payment_id: UUID
    destination_address: str
    amount: float
    currency: str
    blockchain: str
    status: str
    estimated_time_minutes: int = 5
    network_fee: Optional[float]


class BalanceSummaryResponse(BaseModel):
    """User's USDT balance summary."""
    user_id: UUID
    total_balance_usdt: float
    pending_deposits_usdt: float
    pending_withdrawals_usdt: float
    available_balance_usdt: float
    wallets: list[dict] = Field(default_factory=list)


class WalletBalanceResponse(BaseModel):
    """Balance for a specific wallet."""
    wallet_id: UUID
    address: str
    blockchain: str
    usdt_balance: float
    is_primary: bool
