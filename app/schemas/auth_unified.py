"""Unified authentication schemas for TON Wallet and Telegram auth."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AuthMethodEnum(str, Enum):
    """Supported authentication methods."""
    TELEGRAM = "telegram"
    TON_WALLET = "ton_wallet"
    EMAIL = "email"


class InitDataSource(str, Enum):
    """Source of initData - determines validation method."""
    TELEGRAM = "telegram"
    TON_CONNECT = "ton_connect"


class IdentityData(BaseModel):
    """Unified identity data from any auth source."""
    source: InitDataSource
    user_id: str  # Telegram ID or TON wallet address
    raw_data: Dict[str, Any] = Field(default_factory=dict)  # Original payload for audit
    
    # Common fields (mapped from source)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Source-specific fields
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None
    ton_wallet_address: Optional[str] = None
    ton_wallet_metadata: Optional[Dict[str, Any]] = None
    
    # Validation
    auth_date: Optional[int] = None
    hash: Optional[str] = None
    
    class Config:
        use_enum_values = True


class TokenResponse(BaseModel):
    """Token response from authentication."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours in seconds
    refresh_token: Optional[str] = None


class UserIdentityResponse(BaseModel):
    """User identity information returned after auth."""
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: bool
    user_role: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class WalletIdentityResponse(BaseModel):
    """Wallet identity information returned after TON connection."""
    id: str
    wallet_address: str
    status: str
    is_primary: bool
    connected_at: Optional[datetime] = None
    wallet_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class SystemWalletResponse(BaseModel):
    """Response for system wallet info after TON connection."""
    id: str
    user_id: str
    wallet_address: str
    blockchain: str
    wallet_type: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuthSuccessResponse(BaseModel):
    """Unified response for successful authentication."""
    success: bool = True
    auth_method: AuthMethodEnum
    user: UserIdentityResponse
    tokens: TokenResponse
    wallets: Optional[list[WalletIdentityResponse | SystemWalletResponse]] = None
    redirect_url: str = "/dashboard"
    message: str = "Authentication successful"


class AuthErrorResponse(BaseModel):
    """Unified error response."""
    success: bool = False
    error_code: str
    message: str
    details: Optional[str] = None
    
    class Config:
        use_enum_values = True


# Request schemas

class InitDataValidationRequest(BaseModel):
    """Request to validate init data from any source."""
    source: InitDataSource
    init_data: str  # URL-encoded init data string
    signature: Optional[str] = None


class TelegramAuthRequest(BaseModel):
    """Telegram WebApp authentication request."""
    init_data: str  # URL-encoded Telegram init data


class TONWalletAuthRequest(BaseModel):
    """TON wallet connection authentication request."""
    session_id: str
    wallet_address: str
    init_data: str  # Telegram init data for extra validation
    tonconnect_session: Optional[Dict[str, Any]] = None
    wallet_metadata: Optional[Dict[str, Any]] = None


class WalletConnectionRequest(BaseModel):
    """Request to initiate wallet connection."""
    blockchain: str
    wallet_type: str = "custodial"


class WalletDisconnectionRequest(BaseModel):
    """Request to disconnect a wallet."""
    wallet_id: str
