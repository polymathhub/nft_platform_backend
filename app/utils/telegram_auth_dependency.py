
import logging
from typing import Optional, Dict
from fastapi import Header, HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.database import get_db_session
from app.models import User
from app.schemas.user import UserResponse
from app.utils.telegram_init_data import verify_telegram_init_data
from app.utils.security import hash_password

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_telegram_init_data(
    request: Request,
    x_telegram_init_data: Optional[str] = Header(None),
) -> Dict:
    """
    Extract and verify Telegram initData from request headers.
    
    Header: X-Telegram-Init-Data
    
    Returns:
        Parsed Telegram user data
        
    Raises:
        HTTPException(401): If header missing or verification fails
    """
    # Accept initData from header OR query parameter as fallback
    init_data = x_telegram_init_data or request.query_params.get('init_data')
    if not init_data:
        logger.warning("[Auth] Missing Telegram initData (header or query)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Telegram authentication data"
        )

    # Verify initData signature (5 minute default window)
    telegram_user = verify_telegram_init_data(
        init_data,
        settings.telegram_bot_token,
        max_age_seconds=300,
    )
    
    if not telegram_user:
        logger.warning("[Auth] Telegram initData verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication data"
        )
    
    return telegram_user


async def get_current_user(
    request: Request,
    telegram_user: Dict = Depends(get_telegram_init_data),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get or create user from Telegram data.
    
    Automatically registers user from Telegram if doesn't exist.
    No passwords, no manual signup - completely automatic.
    
    Returns:
        User object from database
        
    Raises:
        HTTPException(401): If Telegram verification failed
        HTTPException(500): If database error
    """
    telegram_id = telegram_user.get('telegram_id')
    
    if not telegram_id:
        logger.error("[Auth] No telegram_id in verified data")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram user data"
        )
    
    try:
        # Try to fetch existing user
        result = await db.execute(
            select(User).where(User.telegram_id == str(telegram_id))
        )
        user = result.scalar_one_or_none()
        
        if user:
            logger.debug(f"[Auth] User found: id={user.id}, telegram_id={telegram_id}")
            # Attach to request.state for downstream use
            try:
                request.state.user = user
            except Exception:
                pass
            return user
        
        # Auto-register new user from Telegram data
        logger.info(f"[Auth] Auto-registering new user from Telegram: telegram_id={telegram_id}")
        
        # Generate username from Telegram data
        username = telegram_user.get('username')
        if not username:
            # Fallback: use first_name + telegram_id
            first_name = telegram_user.get('first_name', 'User')
            username = f"{first_name}_{telegram_id}".lower().replace(' ', '_')[:50]
        
        # Generate email from Telegram data (not required, but useful)
        # Since we don't have real email, use a placeholder
        email = f"tg_{telegram_id}@telegram.local"
        
        # Create new user
        new_user = User(
            email=email,
            username=username,
            full_name=telegram_user.get('first_name', ''),
            telegram_id=str(telegram_id),
            telegram_username=telegram_user.get('username'),
            # No password for Telegram-native users (stateless). Use empty placeholder.
            hashed_password="",
            is_active=True,
        )
        
        db.add(new_user)
        await db.flush()  # Get auto-generated ID
        await db.commit()
        try:
            request.state.user = new_user
        except Exception:
            pass
        
        logger.info(
            f"[Auth] ✅ New user registered: id={new_user.id}, "
            f"telegram_id={telegram_id}, username={username}"
        )
        
        return new_user
    
    except Exception as e:
        logger.error(f"[Auth] Failed to get/create user: {type(e).__name__}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system error"
        )


async def get_current_user_optional(
    x_telegram_init_data: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """
    Get current user if Telegram data provided, otherwise None.
    
    Never raises 401 - returns None if auth fails.
    Useful for endpoints that work with or without authentication.
    
    Returns:
        User object if authenticated, None otherwise
    """
    if not x_telegram_init_data:
        return None
    
    try:
        telegram_user = verify_telegram_init_data(
            x_telegram_init_data,
            settings.telegram_bot_token
        )
        
        if not telegram_user:
            return None
        
        telegram_id = telegram_user.get('telegram_id')
        
        result = await db.execute(
            select(User).where(User.telegram_id == str(telegram_id))
        )
        user = result.scalar_one_or_none()
        
        if user:
            return user
        
        # Auto-register if needed
        username = telegram_user.get('username') or f"user_{telegram_id}"
        email = f"tg_{telegram_id}@telegram.local"
        
        new_user = User(
            email=email,
            username=username,
            full_name=telegram_user.get('first_name', ''),
            telegram_id=str(telegram_id),
            telegram_username=telegram_user.get('username'),
            hashed_password=hash_password("") if callable(hash_password) else "",
            is_active=True,
        )
        
        db.add(new_user)
        await db.commit()
        
        return new_user
    
    except Exception as e:
        logger.warning(f"[Auth] Optional auth failed: {e}")
        return None
