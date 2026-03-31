"""
Security Stub Module - STATELESS TELEGRAM AUTHENTICATION ONLY

⚠️ WARNING: This module is DEPRECATED for production use.

The NFT Platform uses STATELESS TELEGRAM AUTHENTICATION. These functions
are kept for BACKWARD COMPATIBILITY ONLY and should NOT be called.

All authentication is handled via:
  - Telegram WebApp initData (signed by Telegram)
  - X-Telegram-Init-Data header on every request
  - app.utils.telegram_auth_dependency.get_current_user()

These functions exist in case legacy code imports them. If they are called
in production, it indicates a security misconfiguration.

================================================================================
                            DO NOT CALL THESE FUNCTIONS
================================================================================

If you need to authenticate requests:
  1. Use Depends(get_current_user) from app.utils.telegram_auth_dependency
  2. Verify X-Telegram-Init-Data header is present
  3. Never call these deprecated functions directly

================================================================================
"""

import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    ⚠️ DEPRECATED: Not used with Telegram stateless auth.
    
    This function should NEVER be called in production.
    Telegram authentication doesn't use passwords.
    """
    logger.error(
        "[SECURITY ALERT] hash_password() called - this should not happen! "
        "Use Telegram authentication instead."
    )
    if not password:
        return ""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    ⚠️ DEPRECATED: Not used with Telegram stateless auth.
    
    This function should NEVER be called in production.
    Telegram authentication doesn't use passwords.
    """
    logger.error(
        "[SECURITY ALERT] verify_password() called - this should not happen! "
        "Use Telegram authentication instead."
    )
    return hash_password(plain_password) == hashed_password


def encrypt_sensitive_data(data: str, key: str = None) -> str:
    """
    ⚠️ DEPRECATED: Not implemented for stateless auth.
    
    Returns data unchanged. DO NOT USE for actual encryption.
    
    If you need to encrypt data, implement proper AES-256 encryption.
    """
    logger.error(
        "[SECURITY ALERT] encrypt_sensitive_data() called but not implemented! "
        "Data returned unencrypted!"
    )
    return data


def decrypt_sensitive_data(encrypted_data: str, key: str = None) -> str:
    """
    ⚠️ DEPRECATED: Not implemented for stateless auth.
    
    Returns data unchanged. DO NOT USE for actual decryption.
    """
    logger.error(
        "[SECURITY ALERT] decrypt_sensitive_data() called but not implemented! "
        "Data returned unchanged!"
    )
    return encrypted_data


def create_access_token(subject: str, **kwargs) -> str:
    """
    ⚠️ DEPRECATED: JWT tokens not used.
    
    Returns empty string. Use Telegram authentication instead.
    """
    logger.error(
        "[SECURITY ALERT] create_access_token() called but not implemented! "
        "Use Telegram authentication instead."
    )
    return ""


def create_refresh_token(subject: str, **kwargs) -> str:
    """
    ⚠️ DEPRECATED: JWT tokens not used.
    
    Returns empty string. Use Telegram authentication instead.
    """
    logger.error(
        "[SECURITY ALERT] create_refresh_token() called but not implemented! "
        "Use Telegram authentication instead."
    )
    return ""


def decode_token(token: str, **kwargs):
    """
    ⚠️ DEPRECATED: JWT tokens not used.
    
    Returns None. Use Telegram authentication instead.
    """
    logger.error(
        "[SECURITY ALERT] decode_token() called but not implemented! "
        "Use Telegram authentication instead."
    )
    return None


def verify_token(token: str, **kwargs):
    """
    ⚠️ DEPRECATED: JWT tokens not used.
    
    Returns None. Use Telegram authentication instead.
    """
    logger.error(
        "[SECURITY ALERT] verify_token() called but not implemented! "
        "Use Telegram authentication instead."
    )
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
