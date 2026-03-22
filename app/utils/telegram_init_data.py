
import hmac
import hashlib
import logging
from typing import Optional, Dict
from urllib.parse import parse_qs
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def verify_telegram_init_data(init_data: str, bot_token: str, max_age_seconds: int = 300) -> Optional[Dict]:
 
    if not init_data or not bot_token:
        logger.warning("[Telegram] Missing init_data or bot_token")
        return None
    
    try:
        # Parse query string
        params = parse_qs(init_data)
        
        # Convert from query string format (lists) to normal dict
        data_dict = {k: v[0] if isinstance(v, list) else v for k, v in params.items()}
        
        # Extract and validate hash
        received_hash = data_dict.get('hash')
        if not received_hash:
            logger.warning("[Telegram] No hash in init_data")
            return None
        
        # Remove hash from dict for signature verification
        del data_dict['hash']
        
        # Sort by key and build data-check-string
        # Format: key1=value1\nkey2=value2\n...
        sorted_keys = sorted(data_dict.keys())
        data_check_string = '\n'.join(
            f"{key}={data_dict[key]}" 
            for key in sorted_keys
        )
        
        logger.debug(f"[Telegram] Data check string: {data_check_string[:100]}...")
        
        # Compute HMAC
        # Step 1: Compute secret key = SHA256(bot_token)
        secret_key = hashlib.sha256(bot_token.encode()).digest()

        # Step 2: Compute HMAC-SHA256(secret_key, data_check_string)
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        logger.debug(f"[Telegram] Computed hash: {computed_hash[:16]}...")
        logger.debug(f"[Telegram] Received hash: {received_hash[:16]}...")
        
        # Compare hashes (constant-time comparison to prevent timing attacks)
        if not hmac.compare_digest(computed_hash, received_hash):
            logger.warning("[Telegram] Hash verification failed - invalid signature")
            return None
        
        logger.debug("[Telegram] ✅ Hash verification passed")
        
        # Validate auth_date (prevent replay attacks)
        auth_date_str = data_dict.get('auth_date')
        if auth_date_str:
            try:
                auth_date = int(auth_date_str)
                now = int(datetime.utcnow().timestamp())
                # Use caller-provided max_age_seconds (default 5 minutes)
                if now - auth_date > max_age_seconds:
                    logger.warning(
                        f"[Telegram] Auth data too old: {now - auth_date}s ago (max: {max_age_seconds}s)"
                    )
                    return None
                logger.debug(f"[Telegram] Auth date valid: {now - auth_date}s old")
            except (ValueError, TypeError) as e:
                logger.warning(f"[Telegram] Invalid auth_date: {e}")
                return None
        
        # Parse user data (JSON)
        user_json = data_dict.get('user')
        if not user_json:
            logger.warning("[Telegram] No user data in init_data")
            return None
        
        try:
            user_data = json.loads(user_json)
        except json.JSONDecodeError as e:
            logger.error(f"[Telegram] Failed to parse user JSON: {e}")
            return None
        
        # Validate required user fields
        if not user_data.get('id') or user_data.get('is_bot'):
            logger.warning(f"[Telegram] Invalid user data: {user_data}")
            return None
        
        logger.info(
            f"[Telegram] Verification successful - user_id={user_data['id']}, "
            f"username={user_data.get('username')}"
        )
        
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
