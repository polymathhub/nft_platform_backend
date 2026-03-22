
import hmac
import hashlib
import logging
import os
from typing import Optional, Dict
from urllib.parse import parse_qsl
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def verify_telegram_init_data(init_data: str, bot_token: str, max_age_seconds: int = 300) -> Optional[Dict]:

    if not init_data or not bot_token:
        logger.warning("[Telegram] Missing init_data or bot_token")
        return None

    try:
        logger.debug(f"[Telegram] INIT DATA RAW: {init_data}")

        # Parse raw query string into list of (key, value) preserving exact values
        pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=True)
        data_dict = {k: v for k, v in pairs}

        # Extract and validate hash
        received_hash = data_dict.get('hash')
        if not received_hash:
            logger.warning("[Telegram] No hash in init_data")
            return None

        # Remove hash for data_check_string
        data_for_check = {k: v for k, v in data_dict.items() if k != 'hash'}

        # Build data-check-string from sorted keys
        sorted_items = sorted(data_for_check.items(), key=lambda kv: kv[0])
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted_items)

        logger.debug(f"[Telegram] DATA CHECK STRING: {data_check_string}")

        # Compute HMAC as per Telegram docs
        secret_key = hashlib.sha256(bot_token.encode('utf-8')).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()

        logger.debug(f"[Telegram] COMPUTED HASH: {computed_hash}")
        logger.debug(f"[Telegram] RECEIVED HASH: {received_hash}")

        # Constant-time comparison
        if not hmac.compare_digest(computed_hash, received_hash):
            logger.warning("[Telegram] Hash verification failed - invalid signature")
            return None

        logger.debug("[Telegram] ✅ Hash verification passed")

        # Validate auth_date (prevent replay attacks)
        auth_date_str = data_for_check.get('auth_date')
        if auth_date_str:
            try:
                auth_date = int(auth_date_str)
                now = int(datetime.utcnow().timestamp())
                if now - auth_date > max_age_seconds:
                    logger.warning(f"[Telegram] Auth data too old: {now - auth_date}s ago (max: {max_age_seconds}s)")
                    return None
                logger.debug(f"[Telegram] Auth date valid: {now - auth_date}s old")
            except (ValueError, TypeError) as e:
                logger.warning(f"[Telegram] Invalid auth_date: {e}")
                return None

        # Parse user JSON
        user_json = data_for_check.get('user')
        if not user_json:
            logger.warning("[Telegram] No user data in init_data")
            return None

        try:
            user_data = json.loads(user_json)
        except json.JSONDecodeError as e:
            logger.error(f"[Telegram] Failed to parse user JSON: {e}")
            return None

        if not user_data.get('id') or user_data.get('is_bot'):
            logger.warning(f"[Telegram] Invalid user data: {user_data}")
            return None

        logger.info(f"[Telegram] Verification successful - user_id={user_data['id']}, username={user_data.get('username')}")

        return {
            'telegram_id': user_data['id'],
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'username': user_data.get('username'),
            'language_code': user_data.get('language_code'),
            'is_premium': user_data.get('is_premium', False),
            'photo_url': user_data.get('photo_url'),
            'allows_write_to_pm': user_data.get('allows_write_to_pm', False),
        }

    except Exception as e:
        logger.error(f"[Telegram] Verification error: {type(e).__name__}: {e}")
        return None


def get_telegram_user_display_name(telegram_user: Dict) -> str:
    """Get display name from Telegram user data."""
    first_name = telegram_user.get('first_name', '')
    last_name = telegram_user.get('last_name', '')
    username = telegram_user.get('username')
    
    name = f"{first_name} {last_name}".strip()
    if not name and username:
        return f"@{username}"
    return name or "User"
