import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from jose import jwt, JWTError
from app.config import get_settings
logger = logging.getLogger(__name__)
settings = get_settings()
class UnifiedTokenService:
    ACCESS_TOKEN_EXPIRE_HOURS = 24
    REFRESH_TOKEN_EXPIRE_DAYS = 30
    ALGORITHM = "HS256"
    @classmethod
    def _get_secret_key(cls) -> str:
        secret = settings.secret_key
        if not secret:
            raise ValueError("SECRET_KEY not configured")
        return secret
    @classmethod
    def generate_tokens(
        cls,
        user_id: str | UUID,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        try:
            user_id_str = str(user_id)
            access_token_payload = {
                "sub": user_id_str,
                "type": "access",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(hours=cls.ACCESS_TOKEN_EXPIRE_HOURS),
            }
            if additional_claims:
                access_token_payload.update(additional_claims)
            access_token = jwt.encode(
                access_token_payload,
                cls._get_secret_key(),
                algorithm=cls.ALGORITHM,
            )
            refresh_token_payload = {
                "sub": user_id_str,
                "type": "refresh",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS),
            }
            refresh_token = jwt.encode(
                refresh_token_payload,
                cls._get_secret_key(),
                algorithm=cls.ALGORITHM,
            )
            logger.debug(f"Tokens generated for user {user_id_str}")
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": cls.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            }
        except Exception as e:
            logger.error(f"Error generating tokens: {e}", exc_info=True)
            raise
    @classmethod
    def verify_access_token(
        cls,
        token: str,
    ) -> Optional[str]:
        try:
            payload = jwt.decode(
                token,
                cls._get_secret_key(),
                algorithms=[cls.ALGORITHM],
            )
            if payload.get("type") != "access":
                logger.warning(f"Invalid token type in payload: {payload.get('type')}")
                return None
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("No 'sub' claim in token")
                return None
            logger.debug(f"Access token verified for user {user_id}")
            return user_id
        except JWTError as e:
            if "expired" in str(e).lower():
                logger.debug("Token has expired")
            else:
                logger.debug(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}", exc_info=True)
            return None
    @classmethod
    def verify_refresh_token(
        cls,
        token: str,
    ) -> Optional[str]:
        try:
            payload = jwt.decode(
                token,
                cls._get_secret_key(),
                algorithms=[cls.ALGORITHM],
            )
            if payload.get("type") != "refresh":
                logger.warning(f"Invalid token type: expected 'refresh', got {payload.get('type')}")
                return None
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("No 'sub' claim in refresh token")
                return None
            logger.debug(f"Refresh token verified for user {user_id}")
            return user_id
        except JWTError as e:
            if "expired" in str(e).lower():
                logger.debug("Refresh token has expired")
            else:
                logger.debug(f"Invalid refresh token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying refresh token: {e}", exc_info=True)
            return None
    @classmethod
    def refresh_access_token(
        cls,
        refresh_token: str,
    ) -> Optional[Dict[str, str]]:
        user_id = cls.verify_refresh_token(refresh_token)
        if not user_id:
            logger.warning("Failed to verify refresh token")
            return None
        try:
            tokens = cls.generate_tokens(user_id)
            return {
                "access_token": tokens["access_token"],
                "token_type": "bearer",
                "expires_in": cls.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            }
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            return None
    @classmethod
    def decode_token_claims(
        cls,
        token: str,
        verify: bool = False,
    ) -> Optional[Dict[str, Any]]:
        try:
            if verify:
                payload = jwt.decode(
                    token,
                    cls._get_secret_key(),
                    algorithms=[cls.ALGORITHM],
                )
            else:
                payload = jwt.decode(
                    token,
                    options={"verify_signature": False},
                )
            return payload
        except Exception as e:
            logger.debug(f"Error decoding token: {e}")
            return None
