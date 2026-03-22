"""
Telegram auth router (v2) - stateless Telegram initData authentication
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session
from app.models import User
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.utils.telegram_init_data import verify_telegram_init_data
from app.utils.telegram_auth_dependency import get_current_user
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["telegram authentication"])
settings = get_settings()


@router.post("/telegram", response_model=dict)
async def telegram_auth(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    init_data_str = body.get("init_data")
    if not init_data_str:
        raise HTTPException(status_code=400, detail="Missing init_data")
    verified = verify_telegram_init_data(init_data_str, settings.telegram_bot_token)
    if not verified:
        raise HTTPException(status_code=401, detail="Telegram verification failed")
    telegram_id = verified.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Missing telegram_id in initData")
    user, err = await AuthService.authenticate_telegram(
        db=db,
        telegram_id=int(telegram_id),
        telegram_username=str(verified.get("username") or ''),
        first_name=str(verified.get("first_name") or ''),
        last_name=str(verified.get("last_name") or ''),
    )
    if err or not user:
        logger.error(f"[Telegram Auth] Failed to get/create user: {err}")
        raise HTTPException(status_code=500, detail=err or "Failed to create user")
    return {"success": True, "user": UserResponse.model_validate(user), "message": "Authenticated"}


@router.get("/profile", response_model=dict)
async def get_profile(current_user: User = Depends(get_current_user)) -> dict:
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"success": True, "user": UserResponse.model_validate(current_user)}


@router.post("/logout", response_model=dict)
async def logout():
    return {"success": True, "message": "Logged out (client-side)"}
