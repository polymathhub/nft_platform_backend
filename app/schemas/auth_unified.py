from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
class AuthMethodEnum(str, Enum):
    TELEGRAM = "telegram"
    TON_WALLET = "ton_wallet"
    EMAIL = "email"
class InitDataSource(str, Enum):
    TELEGRAM = "telegram"
    TON_CONNECT = "ton_connect"
class IdentityData(BaseModel):
    source: InitDataSource
    user_id: str
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None
    ton_wallet_address: Optional[str] = None
    ton_wallet_metadata: Optional[Dict[str, Any]] = None
    auth_date: Optional[int] = None
    hash: Optional[str] = None
    class Config:
        use_enum_values = True
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    refresh_token: Optional[str] = None
class UserIdentityResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None
    is_verified: bool
    user_role: str
    created_at: datetime
    class Config:
        from_attributes = True
class WalletIdentityResponse(BaseModel):
    id: str
    wallet_address: str
    status: str
    is_primary: bool
    connected_at: Optional[datetime] = None
    wallet_metadata: Optional[Dict[str, Any]] = None
    class Config:
        from_attributes = True
class SystemWalletResponse(BaseModel):
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
    success: bool = True
    auth_method: AuthMethodEnum
    user: UserIdentityResponse
    tokens: TokenResponse
    wallets: Optional[list[WalletIdentityResponse | SystemWalletResponse]] = None
    redirect_url: str = "/dashboard"
    message: str = "Authentication successful"
class AuthErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str
    details: Optional[str] = None
    class Config:
        use_enum_values = True
class InitDataValidationRequest(BaseModel):
    source: InitDataSource
    init_data: str
    signature: Optional[str] = None
class TelegramAuthRequest(BaseModel):
    init_data: str
class TONWalletAuthRequest(BaseModel):
    session_id: str
    wallet_address: str
    init_data: str
    tonconnect_session: Optional[Dict[str, Any]] = None
    wallet_metadata: Optional[Dict[str, Any]] = None
class WalletConnectionRequest(BaseModel):
    blockchain: str
    wallet_type: str = "custodial"
class WalletDisconnectionRequest(BaseModel):
    wallet_id: str
