from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os
import json
class Settings(BaseSettings):
    app_name: str = Field(default="NFT Platform Backend")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")
    database_url: str = Field(...)
    database_echo: bool = Field(default=False)
    redis_url: str = Field(default="redis://localhost:6379/0")
    jwt_secret_key: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24, ge=1)
    refresh_token_expiration_days: int = Field(default=30, ge=1)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v):
        import os
        if v == "${DATABASE_URL}":
            v = os.getenv("DATABASE_URL")
            if not v:
                raise ValueError(
                    "DATABASE_URL is not configured properly. "
                    "Set it in .env file or as environment variable.\n"
                    "Format: postgresql+asyncpg://user:password@hostname:5432/database_name\n"
                    "Contact your system administrator for the correct database URL."
                )
        if not v:
            raise ValueError(
                "DATABASE_URL is required. Set it in .env file or as environment variable.\n"
                "Example:\n"
                "  DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname"
            )
        v = str(v).strip()
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        if "postgresql" in v and "+asyncpg" not in v:
            raise ValueError(
                f"PostgreSQL URL must use asyncpg driver.\n"
                f"Invalid: {v[:60]}...\n"
                f"Expected: postgresql+asyncpg://user:password@host:port/dbname"
            )
        return v
    telegram_bot_token: Optional[str] = Field(default=None)
    telegram_api_id: Optional[str] = Field(default=None)
    telegram_api_hash: Optional[str] = Field(default=None)
    telegram_webhook_url: Optional[str] = Field(default=None)
    telegram_auto_setup_webhook: bool = Field(default=False)
    telegram_webhook_secret: Optional[str] = Field(default=None)
    app_url: Optional[str] = Field(default=None)
    telegram_webapp_url: Optional[str] = Field(default=None)
    banner_image_url: str = Field(default="https://image2url.com/r2/default/images/1771155009572-149f055b-78f0-4595-bfc2-fdd990329354.png")
    @field_validator("telegram_webapp_url", mode="before")
    @classmethod
    def derive_telegram_webapp_url(cls, v, info):
        if v:
            return v
        app_url = info.data.get('app_url')
        if app_url:
            return app_url.rstrip('/') + '/webapp/'
        return "https://nftplatformbackend-production-ee5f.up.railway.app/webapp/"
    ipfs_api_url: str = Field(default="http://localhost:5001")
    ipfs_gateway_url: str = Field(default="https://gateway.pinata.cloud/ipfs")
    ton_rpc_url: str = Field(default="https://toncenter.com/api/v2/jsonRPC")
    ton_workchain: int = Field(default=0)
    solana_rpc_url: str = Field(default="https://api.mainnet-beta.solana.com")
    solana_commitment: str = Field(default="confirmed")
    ethereum_rpc_url: str = Field(default="https://eth.public.blastapi.io")
    bitcoin_rpc_url: str = Field(default="https://blockstream.info/api")
    avalanche_rpc_url: str = Field(default="https://api.avax.network/ext/bc/C/rpc")
    polygon_rpc_url: str = Field(default="https://polygon-rpc.com")
    arbitrum_rpc_url: str = Field(default="https://arb1.arbitrum.io/rpc")
    optimism_rpc_url: str = Field(default="https://mainnet.optimism.io")
    base_rpc_url: str = Field(default="https://mainnet.base.org")
    mnemonic_encryption_key: str = Field(...)
    login_max_attempts: int = Field(default=5, ge=1)
    login_block_minutes: int = Field(default=15, ge=1)
    allowed_origins_str: str = Field(default="")
    
    def __init__(self, **data):
        """Parse complex fields from strings"""
        # Extract fields that need parsing
        provided_origins = data.pop('allowed_origins', None)
        provided_wallets = data.pop('platform_wallets', None)
        provided_private_keys = data.pop('platform_private_keys', None)
        provided_cors_headers = data.pop('cors_allow_headers', None)
        
        # Initialize parent first
        super().__init__(**data)
        
        # Parse allowed_origins
        if provided_origins:
            self.allowed_origins = provided_origins
        else:
            self.allowed_origins = self._parse_origins(self.allowed_origins_str, data)
        
        # Parse platform_wallets
        if provided_wallets:
            self.platform_wallets = provided_wallets
        else:
            self.platform_wallets = self._parse_dict(self.platform_wallets_str, {})
        
        # Parse platform_private_keys
        if provided_private_keys:
            self.platform_private_keys = provided_private_keys
        else:
            self.platform_private_keys = self._parse_dict(self.platform_private_keys_str, {})
        
        # Parse cors_allow_headers
        if provided_cors_headers:
            self.cors_allow_headers = provided_cors_headers
        else:
            self.cors_allow_headers = self._parse_list(self.cors_allow_headers_str, [
                "Content-Type",
                "Authorization",
                "Accept",
                "Origin",
                "X-Requested-With",
                "X-Telegram-Web-App-Data",
                "X-Telegram-Init-Data",
            ])
    
    @property
    def allowed_origins(self) -> list[str]:
        """Get computed allowed origins"""
        if not hasattr(self, '_allowed_origins') or not self._allowed_origins:
            self._allowed_origins = self._parse_origins(self.allowed_origins_str, vars(self))
        return self._allowed_origins
    
    @allowed_origins.setter
    def allowed_origins(self, value: list[str]):
        """Set allowed origins"""
        self._allowed_origins = value
    
    @property
    def platform_wallets(self) -> dict[str, str]:
        """Get computed platform wallets"""
        if not hasattr(self, '_platform_wallets'):
            self._platform_wallets = self._parse_dict(self.platform_wallets_str, {})
        return self._platform_wallets
    
    @platform_wallets.setter
    def platform_wallets(self, value: dict[str, str]):
        """Set platform wallets"""
        self._platform_wallets = value
    
    @property
    def platform_private_keys(self) -> dict[str, str]:
        """Get computed platform private keys"""
        if not hasattr(self, '_platform_private_keys'):
            self._platform_private_keys = self._parse_dict(self.platform_private_keys_str, {})
        return self._platform_private_keys
    
    @platform_private_keys.setter
    def platform_private_keys(self, value: dict[str, str]):
        """Set platform private keys"""
        self._platform_private_keys = value
    
    @property
    def cors_allow_headers(self) -> list[str]:
        """Get computed CORS allow headers"""
        if not hasattr(self, '_cors_allow_headers'):
            self._cors_allow_headers = self._parse_list(self.cors_allow_headers_str, [
                "Content-Type",
                "Authorization",
                "Accept",
                "Origin",
                "X-Requested-With",
                "X-Telegram-Web-App-Data",
                "X-Telegram-Init-Data",
            ])
        return self._cors_allow_headers
    
    @cors_allow_headers.setter
    def cors_allow_headers(self, value: list[str]):
        """Set CORS allow headers"""
        self._cors_allow_headers = value
    
    @staticmethod
    def _parse_dict(v: str, default: dict) -> dict[str, str]:
        """Parse dict from JSON string"""
        v = (v or "").strip()
        if not v or v == "{}":
            return default
        try:
            parsed = json.loads(v)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        return default
    
    @staticmethod
    def _parse_list(v: str, default: list) -> list[str]:
        """Parse list from JSON string or comma-separated values"""
        v = (v or "").strip()
        if not v:
            return default
        if v.startswith('[') and v.endswith(']'):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
        if v:
            return [item.strip() for item in v.split(",") if item.strip()]
        return default
    
    @staticmethod
    def _parse_origins(v: str, data: dict) -> list[str]:
        """Parse origins from string"""
        origins = []
        v = (v or "").strip()
        
        if not v:
            origins = ["http://localhost:3000"]
        elif v.startswith('[') and v.endswith(']'):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    origins = [str(item).strip() for item in parsed if item]
            except (json.JSONDecodeError, ValueError):
                pass
        
        if not origins and v:
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
        
        if not origins:
            origins = ["http://localhost:3000"]
        
        app_url = data.get('app_url')
        if app_url:
            origins.append(app_url)
        
        # ✅ SECURITY FIX: Only add localhost in development environments
        environment = data.get('environment', 'development')
        if environment.lower() in ('development', 'dev', 'local'):
            localhost_origins = [
                "http://localhost",
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000",
            ]
            origins.extend(localhost_origins)
        else:
            # ✅ In production/staging, remove any localhost origins
            origins = [o for o in origins if 'localhost' not in o.lower() and '127.0.0.1' not in o]
        
        seen = set()
        unique_origins = []
        for origin in origins:
            if origin not in seen:
                seen.add(origin)
                unique_origins.append(origin)
        return unique_origins
    
    @field_validator("allowed_origins_str", mode="before")
    @classmethod
    def parse_allowed_origins_str(cls, v):
        """Just pass through the string value as-is"""
        return v or ""
    
    require_https: bool = Field(default=True)
    max_request_size: int = Field(default=10485760)
    api_rate_limit: int = Field(default=100)
    api_rate_limit_window: int = Field(default=60)
    usdt_enabled: bool = Field(default=True)
    usdt_contract_ethereum: str = Field(default="0xdAC17F958D2ee523a2206206994597C13D831ec7")
    usdt_contract_polygon: str = Field(default="0xc2132D05D31c914a87C6611C10748AEb04B58e8F")
    usdt_contract_arbitrum: str = Field(default="0xFd086bC7CD5C481DCC9C85Ebe698Ad90E1B4d4Dd")
    usdt_contract_optimism: str = Field(default="0x94b008aA00579c1307B0EF2c499aD98a8ce58e58")
    usdt_contract_avalanche: str = Field(default="0x9702230A8Ea53601f5aD2f56603AE1BeA3eB2d93")
    usdt_contract_base: str = Field(default="0xfde4C96c1286F4B9D7d4A537B9949cFfDA43a26d")
    usdt_decimals: int = Field(default=6)
    usdt_min_transaction: float = Field(default=1.0)
    # Store JSON strings that will be parsed in __init__
    platform_wallets_str: str = Field(default="{}")
    platform_private_keys_str: str = Field(default="{}")
    commission_rate: float = Field(default=0.02)
    commission_wallet_ton: str = Field(default="TMUSBPnZrpcgjaQM2eyugmoPTDf6EfibFd")
    commission_wallet_trc20: str = Field(default="0x892b8ba9c9566f22217e74d661d95eff56aa2ba6")
    commission_wallet_erc20: str = Field(default="0x892b8ba9c9566f22217e74d661d95eff56aa2ba6")
    commission_wallet_solana: str = Field(default="3PFSpY3MeLXVxzJT7KY8AVSjG99v3dQnDjNwH6msYoAg")
    # SECURITY: Admin password MUST be set via environment variable - no default
    admin_password: str = Field(...)
    cors_allow_headers_str: str = Field(default="")
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=4, ge=1)
    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT secret must be 32+ chars")
        return v
    @field_validator("mnemonic_encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        if not isinstance(v, str) or len(v) != 44:
            raise ValueError("mnemonic_encryption_key must be a 44-char Fernet key")
        return v
    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if v and len(v.strip()) == 0:
            return "redis://localhost:6379/0"
        return v
    @field_validator("telegram_bot_token")
    @classmethod
    def validate_telegram_bot_token(cls, v: Optional[str]) -> Optional[str]:
        if not v or len(v.strip()) == 0:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("TELEGRAM_BOT_TOKEN not configured - Telegram features will not work")
            return None
        if not v.startswith(('3', '4', '5', '6', '7', '8', '9')):
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("TELEGRAM_BOT_TOKEN format may be invalid")
        return v
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
