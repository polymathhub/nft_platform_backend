import logging
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User
logger = logging.getLogger(__name__)


class AuthService:
    """Minimal AuthService tailored for Telegram-native auth.

    - No JWTs, no sessions, no passwords.
    - Only `authenticate_telegram` is implemented and used by the app.
    - Legacy functions that would create tokens are intentionally removed.
    """

    @staticmethod
    async def authenticate_telegram(
        db: AsyncSession,
        telegram_id: int,
        telegram_username: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        result = await db.execute(
            select(User).where(User.telegram_id == str(telegram_id))
        )
        user = result.scalar_one_or_none()
        if user:
            if not user.is_active:
                return None, "User account is disabled"
            return user, None

        # Auto-register new Telegram-only user
        email = f"telegram_{telegram_id}@nftplatform.local"
        username = telegram_username or f"user_{telegram_id}"
        full_name = f"{first_name or ''} {last_name or ''}".strip()
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

        new_user = User(
            email=email,
            username=username,
            telegram_id=str(telegram_id),
            telegram_username=telegram_username,
            full_name=full_name,
            hashed_password="",
            is_verified=True,
            is_active=True,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user, None
