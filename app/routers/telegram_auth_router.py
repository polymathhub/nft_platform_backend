"""
Telegram WebApp Authentication Router

This router handles authentication purely through Telegram WebApp initData verification.
No passwords, no JWT tokens, no refresh tokens - just Telegram user identity.

Flow:
1. Frontend reads window.Telegram.WebApp.initData
2. Frontend POSTs initData to /api/auth/telegram
3. Backend validates initData using HMAC-SHA256 with bot token
4. Backend creates/fetches user from DB
5. Backend sets httpOnly session cookie
6. Frontend uses session cookie for all subsequent requests
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db_session
from app.models import User
from app.services.auth_service import AuthService
from app.schemas.user import UserResponse
from app.utils.telegram_security import verify_telegram_data
from app.utils.telegram_init_data import verify_telegram_init_data
import sqlite3
from app.config import get_settings
from datetime import datetime, timedelta
import json
import secrets

logger = logging.getLogger(__name__)
router = APIRouter(tags=["telegram authentication"])
settings = get_settings()

# Simple in-memory session store
# In production, use Redis or database
_SESSION_STORE: Dict[str, Dict] = {}


def _create_session(user_id: str) -> str:
    """Create a session ID and store user association."""
    session_id = secrets.token_urlsafe(32)
    _SESSION_STORE[session_id] = {
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
    }
    return session_id


def _get_user_from_session(session_id: str) -> Optional[str]:
    """Retrieve user_id from session."""
    if not session_id or session_id not in _SESSION_STORE:
        return None
    
    session = _SESSION_STORE[session_id]
    expires_at = datetime.fromisoformat(session["expires_at"])
    
    if datetime.utcnow() > expires_at:
        del _SESSION_STORE[session_id]
        return None
    
    return session["user_id"]


async def get_current_user_from_session(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Dependency that extracts user from session cookie.
    Raises 401 if no valid session found.
    """
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        logger.warning("[Auth] Missing session cookie")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session found"
        )
    
    user_id = _get_user_from_session(session_id)
    
    if not user_id:
        logger.warning("[Auth] Invalid or expired session")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    
    # Fetch user from database
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        logger.error(f"[Auth] User not found: user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.debug(f"[Auth] Session user resolved: id={user.id} username={user.username}")
    return user


@router.post("/telegram", response_model=dict)
async def telegram_auth(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Authenticate using Telegram WebApp initData.
    
    Expected request body:
    {
        "init_data": "query_id=...&user=...&..."  # Raw initData string from Telegram WebApp
    }
    
    Returns user object and sets httpOnly session cookie.
    """
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"[Telegram Auth] Invalid JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    init_data_str = body.get("init_data")
    
    if not init_data_str:
        logger.warning("[Telegram Auth] Missing init_data in request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing init_data"
        )
    
    # Parse init_data query string into dict
    from urllib.parse import parse_qs
    try:
        parsed = parse_qs(init_data_str)
        telegram_data = {k: v[0] if isinstance(v, list) else v for k, v in parsed.items()}
    except Exception as e:
        logger.error(f"[Telegram Auth] Failed to parse init_data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid init_data format"
        )
    
    # Verify Telegram signature
    if not verify_telegram_data(telegram_data):
        logger.warning(
            f"[Telegram Auth] Signature verification failed | "
            f"telegram_id={telegram_data.get('user', {}).get('id') if isinstance(telegram_data.get('user'), dict) else 'unknown'}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram verification failed"
        )
    
    # Parse user data from initData
    user_data_raw = telegram_data.get("user")
    
    if isinstance(user_data_raw, str):
        try:
            user_data = json.loads(user_data_raw)
        except json.JSONDecodeError:
            logger.error("[Telegram Auth] Failed to parse user JSON from initData")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user data in initData"
            )
    elif isinstance(user_data_raw, dict):
        user_data = user_data_raw
    else:
        logger.error(f"[Telegram Auth] Unexpected user data type: {type(user_data_raw)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user data format"
        )
    
    # Extract Telegram user info
    telegram_id = user_data.get("id") or telegram_data.get("telegram_id")
    telegram_username = user_data.get("username") or ""
    first_name = user_data.get("first_name") or ""
    last_name = user_data.get("last_name") or ""
    
    if not telegram_id:
        logger.error("[Telegram Auth] No telegram_id in user data")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing telegram_id"
        )
    
    # Authenticate with Telegram (creates user if doesn't exist)
    user, error = await AuthService.authenticate_telegram(
        db=db,
        telegram_id=int(telegram_id),
        telegram_username=str(telegram_username),
        first_name=str(first_name),
        last_name=str(last_name),
    )
    
    if error:
        logger.error(f"[Telegram Auth] Authentication failed: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Create session
    session_id = _create_session(str(user.id))
    
    # Set httpOnly session cookie (cannot be accessed by JavaScript)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,  # Prevent JavaScript access
        secure=settings.environment == "production",  # Only HTTPS in production
        samesite="Lax",  # Reasonable CSRF protection
        max_age=30 * 24 * 3600,  # 30 days
    )
    
    logger.info(
        f"[Telegram Auth] Successful | "
        f"user_id={user.id} | "
        f"telegram_id={telegram_id} | "
        f"username={telegram_username}"
    )
    
    return {
        "success": True,
        "user": UserResponse.model_validate(user),
        "message": "Authenticated with Telegram"
    }


@router.post("/logout", response_model=dict)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Logout: Clear session cookie.
    No token revocation needed since we use sessions.
    """
    session_id = request.cookies.get("session_id")
    
    if session_id and session_id in _SESSION_STORE:
        del _SESSION_STORE[session_id]
        logger.info(f"[Auth] Session terminated: {session_id}")
    
    # Clear cookie
    response.delete_cookie(
        key="session_id",
        httponly=True,
        secure=settings.environment == "production",
        samesite="Lax",
    )
    
    return {
        "success": True,
        "message": "Logged out successfully"
    }


@router.get("/profile", response_model=dict)
async def get_profile(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get current user profile.
    
    Supports TWO authentication methods:
    1. Session-based (legacy): Requires session_id cookie
    2. Stateless (new): Requires X-Telegram-Init-Data header
    
    This endpoint acts as a bridge for backwards compatibility.
    """
    from app.utils.telegram_security import verify_telegram_data
    from typing import Optional
    
    # Try method 1: Session-based auth (legacy)
    session_id = request.cookies.get("session_id")
    if session_id:
        user_id = _get_user_from_session(session_id)
        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                logger.debug(f"[Auth] GET /profile - session user: id={user.id} username={user.username}")
                return {
                    "success": True,
                    "user": UserResponse.model_validate(user),
                    "message": "Profile retrieved successfully (session-based)"
                }
    
    # Try method 2: Stateless Telegram auth (new)
    x_telegram_init_data: Optional[str] = request.headers.get("x-telegram-init-data")
    if x_telegram_init_data:
        try:
            telegram_user = verify_telegram_init_data(x_telegram_init_data, settings.telegram_bot_token)
            if telegram_user and telegram_user.get('telegram_id'):
                telegram_id = str(telegram_user.get('telegram_id'))
                try:
                    result = await db.execute(
                        select(User).where(User.telegram_id == telegram_id)
                    )
                    user = result.scalar_one_or_none()
                    if user:
                        logger.debug(f"[Auth] GET /profile - stateless user: id={user.id} telegram_id={telegram_id}")
                        return {
                            "success": True,
                            "user": UserResponse.model_validate(user),
                            "message": "Profile retrieved successfully (stateless)"
                        }
                    # Auto-create user if not found
                    logger.info(f"[Auth] Auto-creating user for telegram_id={telegram_id}")
                    new_user, err = await AuthService.authenticate_telegram(
                        db=db,
                        telegram_id=int(telegram_id),
                        telegram_username=str(telegram_user.get('username') or ''),
                        first_name=str(telegram_user.get('first_name') or ''),
                        last_name=str(telegram_user.get('last_name') or ''),
                    )
                    if new_user:
                        logger.info(f"[Auth] Created user id={new_user.id} telegram_id={telegram_id}")
                        return {
                            "success": True,
                            "user": UserResponse.model_validate(new_user),
                            "message": "Profile retrieved successfully (created)"
                        }
                except Exception as db_exc:
                    # DB operation failed - fallback to lightweight SQLite storage
                    logger.warning(f"[Auth] DB error in /profile, falling back to sqlite: {db_exc}")
                    try:
                        conn = sqlite3.connect('local_users.sqlite')
                        cur = conn.cursor()
                        cur.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            telegram_id TEXT UNIQUE,
                            username TEXT,
                            first_name TEXT,
                            photo_url TEXT
                        )
                        ''')
                        conn.commit()
                        cur.execute('SELECT id, telegram_id, username, first_name, photo_url FROM users WHERE telegram_id = ?', (telegram_id,))
                        row = cur.fetchone()
                        if row:
                            user_obj = {
                                'id': row[0],
                                'telegram_id': row[1],
                                'username': row[2],
                                'first_name': row[3],
                                'photo_url': row[4],
                            }
                            conn.close()
                            return {
                                'success': True,
                                'user': user_obj,
                                'message': 'Profile retrieved from sqlite fallback'
                            }
                        # Insert new user into sqlite
                        cur.execute('INSERT INTO users (telegram_id, username, first_name, photo_url) VALUES (?, ?, ?, ?)', (
                            telegram_id,
                            telegram_user.get('username') or f'user_{telegram_id}',
                            telegram_user.get('first_name') or '',
                            telegram_user.get('photo_url') or None,
                        ))
                        conn.commit()
                        uid = cur.lastrowid
                        conn.close()
                        return {
                            'success': True,
                            'user': {
                                'id': uid,
                                'telegram_id': telegram_id,
                                'username': telegram_user.get('username') or f'user_{telegram_id}',
                                'first_name': telegram_user.get('first_name') or '',
                                'photo_url': telegram_user.get('photo_url') or None,
                            },
                            'message': 'Profile created in sqlite fallback'
                        }
                    except Exception as sqlite_exc:
                        logger.error(f"[Auth] Sqlite fallback failed: {sqlite_exc}")
                        # allow outer handler to return 401 below
                        pass
        except Exception as e:
            logger.warning(f"[Auth] Telegram verification failed in /profile: {e}")
    
    # Neither auth method worked
    logger.warning("[Auth] GET /profile - no valid auth method found")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated - provide session cookie or X-Telegram-Init-Data header"
    )


@router.get("/me", response_model=dict)
async def get_me(
    current_user: User = Depends(get_current_user_from_session),
) -> dict:
    """
    Get current user info (alternative endpoint to /profile).
    Requires valid session.
    """
    return {
        "success": True,
        "user": UserResponse.model_validate(current_user),
        "message": "User info retrieved successfully"
    }


@router.get("/check", response_model=dict)
async def check_auth():
    """
    Check if authentication is available (no auth required).
    Useful for frontend to detect if Telegram WebApp is available.
    """
    return {
        "success": True,
        "telegram_available": bool(settings.telegram_bot_token),
        "authentication_enabled": True,
        "message": "Authentication check complete"
    }
