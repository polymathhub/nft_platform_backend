import hashlib
import hmac
import time
import logging
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs
from app.config import get_settings
from app.schemas.auth_unified import IdentityData, InitDataSource
logger = logging.getLogger(__name__)
settings = get_settings()
class UnifiedSecurityService:
    @staticmethod
    def verify_telegram_initdata(
        init_data_str: str,
        bot_token: Optional[str] = None,
        max_age_seconds: int = 86400,
    ) -> Tuple[bool, Optional[str]]:
        if not bot_token:
            bot_token = settings.telegram_bot_token
        if not bot_token:
            return False, "Telegram bot token not configured"
        try:
            data = UnifiedSecurityService.parse_initdata(init_data_str)
            if not data:
                return False, "Failed to parse initData"
            hash_received = data.pop("hash", None)
            if not hash_received:
                return False, "Missing hash in initData"
            auth_date_str = data.get("auth_date")
            if not auth_date_str:
                return False, "Missing auth_date in initData"
            try:
                auth_date = int(auth_date_str)
            except ValueError:
                return False, "Invalid auth_date format"
            current_time = int(time.time())
            age = current_time - auth_date
            if age > max_age_seconds:
                return False, f"InitData expired (age={age}s, max={max_age_seconds}s)"
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
            if not hmac.compare_digest(computed_hash, hash_received):
                logger.warning(
                    f"Telegram HMAC mismatch | "
                    f"computed={computed_hash[:8]}... | "
                    f"received={hash_received[:8]}..."
                )
                return False, "Invalid signature"
            return True, None
        except Exception as e:
            logger.error(f"Error verifying Telegram initData: {type(e).__name__}: {e}")
            return False, f"Verification error: {str(e)}"
    @staticmethod
    def verify_ton_wallet_address(address: str) -> Tuple[bool, Optional[str]]:
        if not address:
            return False, "Wallet address is required"
        if not (address.startswith("0:") or address.startswith("-1:")):
            return False, f"Invalid TON wallet address format: {address}"
        if len(address) < 64:
            return False, f"Wallet address too short: {address}"
        return True, None
    @staticmethod
    def verify_tonconnect_session(
        session_id: str,
        wallet_address: str,
        init_data_str: Optional[str] = None,
        bot_token: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        is_valid, error = UnifiedSecurityService.verify_ton_wallet_address(wallet_address)
        if not is_valid:
            return False, error
        if init_data_str:
            is_valid, error = UnifiedSecurityService.verify_telegram_initdata(
                init_data_str,
                bot_token
            )
            if not is_valid:
                logger.warning(f"TON Connect: Telegram validation failed: {error}")
        return True, None
    @staticmethod
    def parse_initdata(init_data_str: str) -> Optional[Dict[str, str]]:
        if not init_data_str:
            return None
        try:
            parsed = parse_qs(init_data_str, keep_blank_values=True)
            result = {}
            for key, values in parsed.items():
                result[key] = values[0] if values else ""
            return result
        except Exception as e:
            logger.error(f"Error parsing initData: {e}")
            return None
    @staticmethod
    def parse_user_data(user_json_str: Optional[str]) -> Optional[Dict]:
        if not user_json_str:
            return None
        try:
            import json
            return json.loads(user_json_str)
        except Exception as e:
            logger.error(f"Error parsing user data: {e}")
            return None
    @staticmethod
    def extract_telegram_identity(init_data_str: str) -> Optional[IdentityData]:
        try:
            data = UnifiedSecurityService.parse_initdata(init_data_str)
            if not data:
                logger.warning("Failed to parse initData")
                return None
            user_json = data.get("user")
            user_data = UnifiedSecurityService.parse_user_data(user_json) or {}
            telegram_id = str(user_data.get("id") or data.get("id", ""))
            # USERNAME EXTRACTION FIX: Prioritize user_data.username over fallback
            telegram_username = user_data.get("username") or data.get("username", "") or ""
            telegram_username = telegram_username.strip() if telegram_username else ""
            first_name = user_data.get("first_name") or data.get("first_name", "")
            last_name = user_data.get("last_name") or data.get("last_name", "")
            photo_url = user_data.get("photo_url") or data.get("photo_url")  # Extract avatar from Telegram
            
            if not telegram_id:
                logger.warning("No Telegram ID found in initData")
                return None
            
            logger.info(f"[Security] Extracted Telegram identity: id={telegram_id}, username='{telegram_username}' (present={bool(telegram_username)}), first_name={first_name}, photo_url={'<set>' if photo_url else '<none>'}")
            
            return IdentityData(
                source=InitDataSource.TELEGRAM,
                user_id=telegram_id,
                raw_data=data,
                telegram_id=telegram_id,
                telegram_username=telegram_username,
                first_name=first_name,
                last_name=last_name,
                avatar_url=photo_url,  # Store Telegram photo as avatar
                auth_date=int(data.get("auth_date", "0")),
                hash=data.get("hash"),
            )
        except Exception as e:
            logger.error(f"Error extracting Telegram identity: {e}", exc_info=True)
            return None
    @staticmethod
    def extract_ton_identity(
        wallet_address: str,
        wallet_metadata: Optional[Dict] = None,
    ) -> Optional[IdentityData]:
        try:
            is_valid, error = UnifiedSecurityService.verify_ton_wallet_address(wallet_address)
            if not is_valid:
                logger.warning(f"Invalid TON address: {error}")
                return None
            wallet_short = wallet_address[:8]
            return IdentityData(
                source=InitDataSource.TON_CONNECT,
                user_id=wallet_address,
                raw_data=wallet_metadata or {},
                ton_wallet_address=wallet_address,
                ton_wallet_metadata=wallet_metadata,
                username=f"wallet_{wallet_short}",
            )
        except Exception as e:
            logger.error(f"Error extracting TON identity: {e}", exc_info=True)
            return None
