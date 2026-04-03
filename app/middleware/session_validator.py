"""
Session validation middleware for blockchain wallet operations
Prevents replay attacks and enforces session security
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import AsyncSessionLocal
from app.models.ton_wallet_session import TONWalletSession
from app.models import User
import hashlib
import hmac

logger = logging.getLogger(__name__)


class SessionValidator:
    """Validates wallet sessions and prevents replay attacks"""
    
    def __init__(self):
        """Initialize session validator"""
        logger.info("SessionValidator initialized")
    
    async def validate_session(
        self,
        user_id: str,
        session_hash: str,
        public_key: Optional[str] = None
    ) -> bool:
        """
        Validate a wallet session
        
        Args:
            user_id: User UUID
            session_hash: Session hash to verify
            public_key: Public key for signature verification
            
        Returns:
            True if session is valid, False otherwise
            
        Raises:
            HTTPException: If session is invalid or expired
        """
        if not session_hash:
            logger.warning(f"Session validation failed for user {user_id}: missing session_hash")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing session identifier"
            )
        
        async with AsyncSessionLocal() as session:
            # Find active session
            query = select(TONWalletSession).where(
                (TONWalletSession.user_id == user_id) &
                (TONWalletSession.session_hash == session_hash) &
                (TONWalletSession.is_active == True)
            )
            
            result = await session.execute(query)
            wallet_session = result.scalar_one_or_none()
            
            if not wallet_session:
                logger.warning(f"Session validation failed: session not found for user {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session"
                )
            
            # Check if session has expired
            if wallet_session.expires_at and wallet_session.expires_at < datetime.utcnow():
                logger.warning(f"Session expired for user {user_id}: {wallet_session.id}")
                wallet_session.is_active = False
                await session.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired, please reconnect wallet"
                )
            
            # Verify public key if provided
            if public_key and wallet_session.public_key:
                if not await self._verify_public_key(wallet_session.public_key, public_key):
                    logger.warning(f"Public key verification failed for session {wallet_session.id}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Public key verification failed"
                    )
            
            # Update last activity
            wallet_session.last_activity_at = datetime.utcnow()
            wallet_session.transaction_count = (wallet_session.transaction_count or 0) + 1
            await session.commit()
            
            return True
    
    async def create_session_hash(
        self,
        user_id: str,
        wallet_address: str,
        device_info: dict
    ) -> str:
        """
        Create a replay-attack-resistant session hash
        
        Args:
            user_id: User UUID
            wallet_address: TON wallet address
            device_info: Device information for fingerprinting
            
        Returns:
            Session hash
        """
        # Create composite key from user, wallet, and device info
        device_string = (
            f"{device_info.get('platform', 'unknown')}"
            f"|{device_info.get('name', 'unknown')}"
            f"|{device_info.get('app', 'unknown')}"
        )
        
        # Combine all elements with timestamp
        composite = f"{user_id}|{wallet_address}|{device_string}|{datetime.utcnow().isoformat()}"
        
        # Generate hash
        session_hash = hashlib.sha256(composite.encode()).hexdigest()
        
        logger.debug(f"Generated session hash for user {user_id}")
        return session_hash
    
    async def _verify_public_key(
        self,
        stored_key: str,
        provided_key: str
    ) -> bool:
        """
        Verify that provided public key matches stored key
        
        Args:
            stored_key: Key stored in database
            provided_key: Key provided in request
            
        Returns:
            True if keys match, False otherwise
        """
        # Simple comparison - in production, might use HMAC or signature verification
        return hashlib.sha256(provided_key.encode()).hexdigest() == stored_key
    
    async def invalidate_session(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> int:
        """
        Invalidate user sessions (all or specific)
        
        Args:
            user_id: User UUID
            session_id: Specific session to invalidate (if None, invalidates all)
            
        Returns:
            Number of sessions invalidated
        """
        async with AsyncSessionLocal() as db_session:
            if session_id:
                query = select(TONWalletSession).where(
                    (TONWalletSession.user_id == user_id) &
                    (TONWalletSession.id == session_id)
                )
            else:
                query = select(TONWalletSession).where(
                    TONWalletSession.user_id == user_id
                )
            
            result = await db_session.execute(query)
            sessions = result.scalars().all()
            
            count = len(sessions)
            for session_record in sessions:
                session_record.is_active = False
            
            await db_session.commit()
            logger.info(f"Invalidated {count} session(s) for user {user_id}")
            
            return count
    
    async def get_active_sessions(self, user_id: str) -> list:
        """
        Get all active sessions for a user
        
        Args:
            user_id: User UUID
            
        Returns:
            List of active sessions
        """
        async with AsyncSessionLocal() as session:
            query = select(TONWalletSession).where(
                (TONWalletSession.user_id == user_id) &
                (TONWalletSession.is_active == True) &
                ((TONWalletSession.expires_at.is_(None)) |
                 (TONWalletSession.expires_at > datetime.utcnow()))
            )
            
            result = await session.execute(query)
            sessions = result.scalars().all()
            
            return [
                {
                    "id": str(s.id),
                    "device": f"{s.device_platform} - {s.device_name}",
                    "app": s.app_name,
                    "created_at": s.created_at.isoformat(),
                    "last_activity": s.last_activity_at.isoformat(),
                    "transaction_count": s.transaction_count
                }
                for s in sessions
            ]


# Global session validator instance
_session_validator = SessionValidator()


def get_session_validator() -> SessionValidator:
    """Get the global session validator"""
    return _session_validator


async def require_valid_session(request: Request) -> dict:
    """
    Dependency for FastAPI endpoints that require valid session
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Session data if valid
        
    Raises:
        HTTPException: If session is invalid
    """
    # Extract session info from headers or cookies
    session_hash = request.headers.get("X-Session-Hash")
    public_key = request.headers.get("X-Public-Key")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id or not session_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session credentials"
        )
    
    #Validate session
    validator = get_session_validator()
    await validator.validate_session(user_id, session_hash, public_key)
    
    return {
        "user_id": user_id,
        "session_hash": session_hash,
        "public_key": public_key
    }


class SessionValidationMiddleware:
    """ASGI middleware for session validation on protected endpoints"""
    
    PROTECTED_PATHS = [
        "/api/v1/blockchain/",
        "/api/v1/wallets/",
        "/api/v1/nfts/mint",
    ]
    
    def __init__(self, app):
        """Initialize middleware"""
        self.app = app
        self.validator = get_session_validator()
        logger.info("SessionValidationMiddleware initialized")
    
    async def __call__(self, scope, receive, send):
        """Process request through middleware"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        path = scope["path"]
        method = scope["method"]
        
        # Skip validation for non-protected paths
        if not self._is_protected_path(path):
            await self.app(scope, receive, send)
            return
        
        # Skip validation for certain methods
        if method in ["GET", "HEAD", "OPTIONS"]:
            await self.app(scope, receive, send)
            return
        
        # Create request object to access headers
        from starlette.requests import Request
        request = Request(scope, receive)
        
        try:
            # Validate session
            session_hash = request.headers.get("X-Session-Hash")
            user_id = request.headers.get("X-User-ID")
            
            if session_hash and user_id:
                await self.validator.validate_session(user_id, session_hash)
                logger.debug(f"Session validated for path: {path}")
            else:
                logger.debug(f"No session headers found for path: {path}")
        
        except HTTPException as e:
            logger.warning(f"Session validation failed for {method} {path}: {e.detail}")
            # Add validation error to scope for handler
            scope["session_validation_error"] = e
        
        # Continue to app
        await self.app(scope, receive, send)
    
    def _is_protected_path(self, path: str) -> bool:
        """Check if path requires session validation"""
        for protected_path in self.PROTECTED_PATHS:
            if path.startswith(protected_path):
                return True
        return False
