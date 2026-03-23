import logging
from typing import Dict, Optional
from fastapi import Header, HTTPException, status, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.database import get_db_session
from app.models import User
from app.utils.telegram_init_data import verify_telegram_init_data

logger = logging.getLogger(__name__)
settings = get_settings()


async def parse_init_data(
    request: Request,
    x_telegram_init_data: Optional[str] = Header(None),
) -> Dict:
    """Extract raw initData from header or query and return parsed Telegram user dict.

    Raises HTTPException(401) on missing/invalid data.
    """
    init_data = x_telegram_init_data or request.query_params.get("init_data")
    if not init_data:
        logger.warning("[TelegramAuth] Missing X-Telegram-Init-Data header")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Telegram initData")

    user = verify_telegram_init_data(init_data, settings.telegram_bot_token, max_age_seconds=300)
    if not user:
        logger.warning("[TelegramAuth] initData verification failed")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram initData")

    return user


async def get_current_telegram_user(
    request: Request,
    telegram_user: Dict = Depends(parse_init_data),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """FastAPI dependency: verify Telegram initData and return DB User (auto-create if missing).

    Returns the SQLAlchemy `User` instance.
    """
    telegram_id = telegram_user.get("telegram_id")
    if not telegram_id:
        logger.error("[TelegramAuth] verified data missing telegram_id")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram user data")

    try:
        result = await db.execute(select(User).where(User.telegram_id == str(telegram_id)))
        user = result.scalar_one_or_none()
        if user:
            try:
                request.state.user = user
            except Exception:
                pass
            return user

        # Auto-register
        username = telegram_user.get("username") or f"tg_{telegram_id}"
        email = f"tg_{telegram_id}@telegram.local"
        new_user = User(
            email=email,
            username=username,
            full_name=telegram_user.get("first_name") or "",
            telegram_id=str(telegram_id),
            telegram_username=telegram_user.get("username"),
            hashed_password="",
            is_active=True,
        )
        db.add(new_user)
        await db.flush()
        await db.commit()
        await db.refresh(new_user)
        try:
            request.state.user = new_user
        except Exception:
            pass
        logger.info(f"[TelegramAuth] Auto-registered user telegram_id={telegram_id} username={username}")
        return new_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TelegramAuth] DB error: {e}")
        try:
            await db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication error")


__all__ = ["parse_init_data", "get_current_telegram_user"]
