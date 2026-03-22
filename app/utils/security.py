"""
Security utilities for password hashing and JWT token management.

Uses:
- passlib[bcrypt] for password hashing
- python-jose for JWT creation and validation
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        password: The plain-text password to hash.

    Returns:
        A bcrypt-hashed string suitable for storage.
    """
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash.

    Args:
        plain_password:  The password provided by the user.
        hashed_password: The bcrypt hash stored in the database.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        return _pwd_context.verify(plain_password, hashed_password)
    except Exception as exc:
        logger.warning("Password verification error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# JWT token creation and validation
# ---------------------------------------------------------------------------

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        data:          Payload claims to embed in the token (e.g. ``{"sub": user_id}``).
        expires_delta: How long until the token expires.  Defaults to the value
                       of ``jwt_expiration_hours`` in app settings.

    Returns:
        A signed JWT string.
    """
    settings = get_settings()

    if expires_delta is None:
        expires_delta = timedelta(hours=settings.jwt_expiration_hours)

    payload = data.copy()
    expire = datetime.utcnow() + expires_delta
    payload.update({"exp": expire, "type": payload.get("type", "access")})

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT refresh token.

    Args:
        data:          Payload claims to embed in the token (e.g. ``{"sub": user_id}``).
        expires_delta: How long until the token expires.  Defaults to the value
                       of ``refresh_token_expiration_days`` in app settings.

    Returns:
        A signed JWT string with ``type`` set to ``"refresh"``.
    """
    settings = get_settings()

    if expires_delta is None:
        expires_delta = timedelta(days=settings.refresh_token_expiration_days)

    payload = data.copy()
    expire = datetime.utcnow() + expires_delta
    payload.update({"exp": expire, "type": "refresh"})

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Args:
        token: The JWT string to decode.

    Returns:
        The decoded payload as a dictionary.

    Raises:
        ValueError: If the token is invalid, expired, or cannot be decoded.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:
        logger.warning("JWT decode error: %s", exc)
        raise ValueError(f"Invalid or expired token: {exc}") from exc
