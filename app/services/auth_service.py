"""
Stateless Auth Service - Telegram Authentication Only

No JWT tokens, sessions, or password authentication.
Auto-registers users from Telegram WebApp initData.
"""

import logging
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User

logger = logging.getLogger(__name__)


class AuthService:
    """Stateless authentication using Telegram WebApp."""

    @staticmethod
    async def authenticate_telegram(
        db: AsyncSession,
        telegram_id: int,
        telegram_username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate or auto-register a Telegram user.
        
        Called when Telegram initData verification succeeds.
        Auto-registers the user if they don't exist yet.
        """
        try:
            # Try to find existing user
            result = await db.execute(
                select(User).where(User.telegram_id == str(telegram_id))
            )
            user = result.scalar_one_or_none()
            
            if user:
                if not user.is_active:
                    return None, "User account is disabled"
                return user, None
            
            # Auto-register new Telegram user
            email = f"telegram_{telegram_id}@nftplatform.local"
            username = telegram_username or f"user_{telegram_id}"
            full_name = f"{first_name or ''} {last_name or ''}".strip()
            
            # Ensure username is unique
            counter = 1
            original_username = username
            while True:
                existing = await db.execute(
                    select(User).where(User.username == username)
                )
                if not existing.scalar_one_or_none():
                    break
                username = f"{original_username}_{counter}"
                counter += 1
            
            # Create new user (no password needed for Telegram auth)
            new_user = User(
                email=email,
                username=username,
                telegram_id=str(telegram_id),
                telegram_username=telegram_username,
                full_name=full_name,
                hashed_password="",
                is_active=True,
                is_verified=True,
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            logger.info(f"[AuthService] Auto-registered Telegram user: {telegram_id} ({username})")
            return new_user, None
            
        except Exception as e:
            logger.error(f"[AuthService] Error in authenticate_telegram: {e}", exc_info=True)
            try:
                await db.rollback()
            except Exception:
                pass
            return None, str(e)
