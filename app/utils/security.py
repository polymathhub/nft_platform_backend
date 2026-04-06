import base64
import hashlib
import logging

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


def _build_fernet(key: str) -> Fernet:
    """Derive a valid 32-byte Fernet key from the provided key string.

    Fernet requires exactly 32 bytes encoded as URL-safe base64 (44 chars
    with padding).  The settings validator already normalises
    ``mnemonic_encryption_key`` to 44 characters, so a correctly configured
    key passes straight through.  As a safety net for any other caller, raw
    strings that are not valid base64 are hashed with SHA-256 to produce a
    stable 32-byte value and then base64-encoded.
    """
    key = key.strip()

    # Happy path: key is already a valid 44-char URL-safe base64 Fernet key.
    if len(key) == 44:
        try:
            raw = base64.urlsafe_b64decode(key)
            if len(raw) == 32:
                return Fernet(key.encode())
        except Exception:
            pass

    # Fallback: derive 32 bytes via SHA-256 and re-encode.
    logger.warning(
        "mnemonic_encryption_key is not a standard Fernet key; "
        "deriving a 32-byte key via SHA-256."
    )
    raw = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(raw)
    return Fernet(fernet_key)


def encrypt_sensitive_data(data: str, key: str) -> str:
    """Encrypt *data* using Fernet symmetric encryption.

    Args:
        data: Plaintext string to encrypt (e.g. a mnemonic or private key).
        key:  Encryption key — typically ``settings.mnemonic_encryption_key``.

    Returns:
        A URL-safe base64-encoded ciphertext string produced by Fernet.
    """
    f = _build_fernet(key)
    token: bytes = f.encrypt(data.encode())
    # Fernet tokens are already URL-safe base64; return as a plain string.
    return token.decode()


def decrypt_sensitive_data(encrypted_data: str, key: str) -> str:
    """Decrypt a Fernet-encrypted ciphertext back to the original string.

    Args:
        encrypted_data: Base64-encoded ciphertext previously produced by
                        :func:`encrypt_sensitive_data`.
        key:            Encryption key — must match the one used to encrypt.

    Returns:
        The original plaintext string.

    Raises:
        cryptography.fernet.InvalidToken: If the token is invalid or the key
        does not match.
    """
    f = _build_fernet(key)
    plaintext: bytes = f.decrypt(encrypted_data.encode())
    return plaintext.decode()
