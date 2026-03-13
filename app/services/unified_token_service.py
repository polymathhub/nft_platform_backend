"""Unified token service for generating and validating JWT tokens across auth sources."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import jwt
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class UnifiedTokenService:
    """
    Unified JWT token generation and validation for all auth sources.
    
    Provides:
    - Consistent token generation (access + refresh)
    - Token validation and decoding
    - Token refresh logic
    - Expiry management
    """

    # Token configuration
    ACCESS_TOKEN_EXPIRE_HOURS = 24
    REFRESH_TOKEN_EXPIRE_DAYS = 30
    ALGORITHM = "HS256"

    @classmethod
    def _get_secret_key(cls) -> str:
        """Get JWT secret key from config."""
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
        """
        Generate access and refresh tokens for a user.
        
        Args:
            user_id: User ID (can be string or UUID)
            additional_claims: Optional additional claims to include
        
        Returns:
            Dict with 'access_token' and 'refresh_token'
        """
        try:
            user_id_str = str(user_id)
            
            # Generate access token
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
            
            # Generate refresh token
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
        """
        Verify and decode access token.
        
        Args:
            token: JWT token string
        
        Returns:
            User ID if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                cls._get_secret_key(),
                algorithms=[cls.ALGORITHM],
            )
            
            # Verify token type
            if payload.get("type") != "access":
                logger.warning(f"Invalid token type in payload: {payload.get('type')}")
                return None
            
            # Extract user ID
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("No 'sub' claim in token")
                return None
            
            logger.debug(f"Access token verified for user {user_id}")
            return user_id
            
        except jwt.ExpiredSignatureError:
            logger.debug("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
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
        """
        Verify and decode refresh token.
        
        Args:
            token: JWT refresh token string
        
        Returns:
            User ID if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                cls._get_secret_key(),
                algorithms=[cls.ALGORITHM],
            )
            
            # Verify token type
            if payload.get("type") != "refresh":
                logger.warning(f"Invalid token type: expected 'refresh', got {payload.get('type')}")
                return None
            
            # Extract user ID
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("No 'sub' claim in refresh token")
                return None
            
            logger.debug(f"Refresh token verified for user {user_id}")
            return user_id
            
        except jwt.ExpiredSignatureError:
            logger.debug("Refresh token has expired")
            return None
        except jwt.InvalidTokenError as e:
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
        """
        Generate new access token from valid refresh token.
        
        Args:
            refresh_token: Valid refresh token
        
        Returns:
            Dict with new 'access_token' or None if refresh token invalid
        """
        # Verify refresh token
        user_id = cls.verify_refresh_token(refresh_token)
        if not user_id:
            logger.warning("Failed to verify refresh token")
            return None
        
        # Generate new access token
        try:
            tokens = cls.generate_tokens(user_id)
            # Return only new access token (keep existing refresh token)
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
        """
        Decode token claims (with or without signature verification).
        
        Args:
            token: JWT token
            verify: If True, verify signature. If False, skip verification (for debugging)
        
        Returns:
            Token claims dict or None if decoding fails
        """
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
