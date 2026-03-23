"""
Security Stub Module

This module provides placeholder implementations for security functions
that are technically needed by legacy code but not used in the 
stateless Telegram authentication flow.
"""

import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Placeholder: hash a password.
    Not usedfor Telegram auth (stateless).
    """
    # For default empty passwords, return empty
    if not password:
        return ""
    # Simple placeholder (NOT FOR PRODUCTION)
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Placeholder: verify a password hash.
    Not used for Telegram auth (stateless).
    """
    return hash_password(plain_password) == hashed_password


def encrypt_sensitive_data(data: str, key: str = None) -> str:
    """
    Placeholder: encrypt sensitive data.
    Returns data as-is (no real encryption).
    """
    logger.warning("[Security] encrypt_sensitive_data called - not implemented for stateless auth")
    return data


def decrypt_sensitive_data(encrypted_data: str, key: str = None) -> str:
    """
    Placeholder: decrypt sensitive data.
    Returns data as-is (no real decryption).
    """
    logger.warning("[Security] decrypt_sensitive_data called - not implemented for stateless auth")
    return encrypted_data


def create_access_token(subject: str, **kwargs) -> str:
    """
    Placeholder: create JWT access token.
    Not used for Telegram auth (stateless).
    """
    logger.warning("[Security] create_access_token called - not implemented for stateless auth")
    return ""


def create_refresh_token(subject: str, **kwargs) -> str:
    """
    Placeholder: create JWT refresh token.
    Not used for Telegram auth (stateless).
    """
    logger.warning("[Security] create_refresh_token called - not implemented for stateless auth")
    return ""


def decode_token(token: str, **kwargs):
    """
    Placeholder: decode JWT token.
    Not used for Telegram auth (stateless).
    """
    logger.warning("[Security] decode_token called - not implemented for stateless auth")
    return None


def verify_token(token: str, **kwargs):
    """
    Placeholder: verify JWT token.
    Not used for Telegram auth (stateless).
    """
    logger.warning("[Security] verify_token called - not implemented for stateless auth")
    return None


__all__ = [
    "hash_password",
    "verify_password",
    "encrypt_sensitive_data",
    "decrypt_sensitive_data",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
]
