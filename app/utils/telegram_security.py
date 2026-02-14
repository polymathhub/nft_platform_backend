import hmac
import hashlib
from typing import Dict, Optional
from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def verify_telegram_data(
    data: Dict[str, str],
    bot_token: Optional[str] = None,
) -> bool:
    if not bot_token:
        settings = get_settings()
        bot_token = settings.telegram_bot_token
    
    if not bot_token:
        logger.warning("Telegram bot token not configured")
        return False
    
    data_hash = data.get("hash")
    if not data_hash:
        logger.warning("No hash in Telegram data")
        return False
    
    check_string_parts = []
    for key in sorted(data.keys()):
        if key != "hash":
            check_string_parts.append(f"{key}={data[key]}")
    
    check_string = "\n".join(check_string_parts)
    
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(
        secret_key,
        check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    is_valid = hmac.compare_digest(computed_hash, data_hash)
    
    if not is_valid:
        logger.warning(f"Invalid Telegram data signature")
    
    return is_valid
