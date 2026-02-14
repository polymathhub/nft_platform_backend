import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any, Dict, Tuple
from uuid import UUID
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Use pbkdf2_sha256 - stable, no external dependencies required for Python 3.11
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__rounds=30000,
)


def hash_password(password: Optional[str]) -> str:
    if not password:
        password = secrets.token_urlsafe(32)
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(
    subject: Union[str, UUID],
    expires_delta: Optional[timedelta] = None,
    secret_key: str = "",
    algorithm: str = "HS256",
) -> str:
    if not secret_key:
        raise ValueError("Secret key required")
    
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=24))
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "jti": secrets.token_urlsafe(16),
    }
    
    try:
        return jwt.encode(to_encode, secret_key, algorithm=algorithm)
    except Exception as e:
        logger.error(f"Token encode error: {e}")
        raise


def create_refresh_token(
    subject: Union[str, UUID],
    expires_delta: Optional[timedelta] = None,
    secret_key: str = "",
    algorithm: str = "HS256",
) -> str:
    if not secret_key:
        raise ValueError("Secret key required")
    
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=30))
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16),
    }
    
    try:
        return jwt.encode(to_encode, secret_key, algorithm=algorithm)
    except Exception as e:
        logger.error(f"Token encode error: {e}")
        raise


def decode_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
) -> Optional[Dict[str, Any]]:
    """Decode JWT - return None if invalid."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        if not payload.get("sub"):
            return None
        return payload
    except JWTError:
        logger.debug("Invalid token")
        return None


def verify_token(token: str, secret_key: str = "", algorithm: str = "HS256") -> Optional[UUID]:
    if not secret_key:
        from app.config import get_settings
        settings = get_settings()
        secret_key = settings.jwt_secret_key
        algorithm = settings.jwt_algorithm
    
    payload = decode_token(
        token,
        secret_key=secret_key,
        algorithm=algorithm,
    )
    if payload:
        try:
            if payload.get("type") != "access":
                return None
            return UUID(payload.get("sub"))
        except (ValueError, TypeError):
            return None
    return None


def encrypt_sensitive_data(data: str, key: str) -> str:
    """Encrypt data with Fernet (AES-128).
    
    Key must be 32 bytes base64-encoded. Handle in config with utility functions.
    """
    try:
        if isinstance(key, str):
            key = key.encode()
        return Fernet(key).encrypt(data.encode()).decode()
    except InvalidToken:
        raise ValueError("Invalid encryption key")
    except Exception as e:
        logger.error(f"Encrypt error: {e}")
        raise

  
def decrypt_sensitive_data(encrypted: str, key: str) -> str:
    """Decrypt Fernet-encrypted data."""
    try:
        if isinstance(key, str):
            key = key.encode()
        return Fernet(key).decrypt(encrypted.encode()).decode()
    except InvalidToken:
        raise ValueError("Decrypt failed - bad key or corrupted data")
    except Exception as e:
        logger.error(f"Decrypt error: {e}")
        raise

