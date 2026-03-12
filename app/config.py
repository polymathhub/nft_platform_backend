from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os
import json


class Settings(BaseSettings):
    app_name: str = Field(default="NFT Platform Backend")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")  # development, staging, production

    database_url: str = Field(...)
    database_echo: bool = Field(default=False)

    redis_url: str = Field(default="redis://localhost:6379/0")

    jwt_secret_key: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24, ge=1)
    refresh_token_expiration_days: int = Field(default=30, ge=1)

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v):
        """
        Validate and sanitize the database URL.
        
        Handles:
        - Literal ${DATABASE_URL} strings (loads from environment)
        - Old postgres:// URLs (converts to postgresql+asyncpg://)
        - Missing URLs (raises clear error)
        """
        import os
        
        # If it's the literal string ${DATABASE_URL}, try to load from environment
        if v == "${DATABASE_URL}":
            v = os.getenv("DATABASE_URL")
            if not v:
                raise ValueError(
                    "DATABASE_URL is set to literal '${DATABASE_URL}' in .env or config. "
                    "Either:\n"
                    "  1. Set DATABASE_URL in .env to actual value (e.g., postgresql+asyncpg://user:pass@host/db)\n"
                    "  2. Or set the DATABASE_URL environment variable before starting the app\n"
                    "Example: export DATABASE_URL='postgresql+asyncpg://nft_user:GiftedForge@5.252.155.82:5432/nft_db'"
                )
        
        if not v:
            raise ValueError(
                "DATABASE_URL is required. Set it in .env file or as environment variable.\n"
                "Example:\n"
                "  DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname"
            )
        
        v = str(v).strip()
        
        # Convert old postgres:// to postgresql+asyncpg://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Ensure asyncpg driver for async operations
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
    telegram_webhook_url: Optional[str] = Field(default=None)  # Ngrok or public URL
    telegram_auto_setup_webhook: bool = Field(default=False)  # Auto-setup webhook on startup
    telegram_webhook_secret: Optional[str] = Field(default=None)  # Secret token for webhook validation
    telegram_webapp_url: str = Field(default="https://nftplatformbackend-production-b67d.up.railway.app/webapp/")  # Telegram Web App URL
    banner_image_url: str = Field(default="https://image2url.com/r2/default/images/1771155009572-149f055b-78f0-4595-bfc2-fdd990329354.png")  # /start banner image (1200x600 for mobile responsiveness)

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

    allowed_origins: list[str] = Field(default=["http://localhost:3000"])
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """
        Parse allowed origins from environment variable.
        Supports:
        - JSON array: ["http://localhost:3000","https://myfrontend.com"]
        - Comma-separated string: http://localhost:3000,https://myfrontend.com
        - Python list: ["http://localhost:3000"]
        """
        if isinstance(v, list):
            # Already a list, return as-is
            return v
        
        if isinstance(v, str):
            v = v.strip()
            
            # Try to parse as JSON array first
            if v.startswith('[') and v.endswith(']'):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if item]
                except (json.JSONDecodeError, ValueError):
                    pass  # Fall through to comma-separated parsing
            
            # Parse as comma-separated string
            if v:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        
        # Default fallback
        return ["http://localhost:3000"]
    
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

    # Platform custodial wallets for receiving deposits, keyed by blockchain name lower-case
    platform_wallets: dict[str, str] = Field(default={})

    # Platform private keys for signing payouts (secret). Map blockchain lower-case -> hex private key (0x...)
    platform_private_keys: dict[str, str] = Field(default={})
    
    # Commission settings
    commission_rate: float = Field(default=0.02)  # 2% default
    commission_wallet_ton: str = Field(default="TMUSBPnZrpcgjaQM2eyugmoPTDf6EfibFd")
    commission_wallet_trc20: str = Field(default="0x892b8ba9c9566f22217e74d661d95eff56aa2ba6")
    commission_wallet_erc20: str = Field(default="0x892b8ba9c9566f22217e74d661d95eff56aa2ba6")
    commission_wallet_solana: str = Field(default="3PFSpY3MeLXVxzJT7KY8AVSjG99v3dQnDjNwH6msYoAg")
    
    # Admin credentials
    admin_password: str = Field(default="Firdavs")
    
    cors_allow_headers: list[str] = Field(default=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-Telegram-Web-App-Data",
        "X-Telegram-Init-Data",
    ])

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
        # Redis is optional for development, defaults to localhost:6379
        if v and len(v.strip()) == 0:
            return "redis://localhost:6379/0"
        return v
    
    @field_validator("telegram_bot_token")
    @classmethod
    def validate_telegram_bot_token(cls, v: Optional[str]) -> Optional[str]:
        # Warning if not configured (optional but recommended)
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False  # Allow TELEGRAM_BOT_TOKEN, telegram_bot_token, etc.


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
