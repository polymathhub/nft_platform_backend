import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db_session
from app.services.auth_service import AuthService
from app.models import User
from typing import Optional

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    if not credentials or not credentials.credentials:
        logger.warning("[Auth] Missing credentials in request")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    token = credentials.credentials
    user_id = AuthService.verify_token(token)
    if not user_id:
        logger.warning("[Auth] Invalid/expired token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.error(f"[Auth] User not found: user_id={user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    logger.debug(f"[Auth] Current user resolved: id={user.id} username={user.username} email={user.email}")
    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """
    Optional authentication - returns user if authenticated, None otherwise
    Never raises 401 Unauthorized
    Useful for endpoints that work with or without authentication
    """
    if not credentials or not credentials.credentials:
        return None
    
    token = credentials.credentials
    user_id = AuthService.verify_token(token)
    
    if not user_id:
        return None
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    logger.debug(f"[Auth] Optional user resolved: id={user.id} username={user.username}")
    return user

