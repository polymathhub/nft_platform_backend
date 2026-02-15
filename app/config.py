from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    app_name: str = Field(default="NFT Platform Backend")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    database_url: str = Field(...)
    database_echo: bool = Field(default=False)

    redis_url: str = Field(...)

    jwt_secret_key: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24, ge=1)
    refresh_token_expiration_days: int = Field(default=30, ge=1)

    telegram_bot_token: Optional[str] = Field(default=None)
    telegram_api_id: Optional[str] = Field(default=None)
    telegram_api_hash: Optional[str] = Field(default=None)
    telegram_webhook_url: Optional[str] = Field(default=None)  # Ngrok or public URL
    telegram_auto_setup_webhook: bool = Field(default=False)  # Auto-setup webhook on startup
    telegram_webhook_secret: Optional[str] = Field(default=None)  # Secret token for webhook validation
    telegram_webapp_url: str = Field(default="https://nftplatformbackend-production-b67d.up.railway.app/web-app/")  # Telegram Web App URL
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
