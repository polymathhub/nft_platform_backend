import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    TelegramLoginRequest,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
)
from app.services.auth_service import AuthService
from app.models import User
from app.utils.rate_limiter import is_blocked, record_failed_attempt, reset_attempts
from app.utils.auth import get_current_user
from app.utils.telegram_security import verify_telegram_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=dict)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db_session),
):
    user, error = await AuthService.register_user(
        db=db,
        email=request.email,
        username=request.username,
        password=request.password,
        full_name=request.full_name,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    tokens = AuthService.generate_tokens(user.id)
    return {
        "user": UserResponse.model_validate(user),
        "tokens": TokenResponse(**tokens),
    }


@router.post("/login", response_model=dict)
async def login(
    request: UserLoginRequest,
    request_obj: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    client_ip = None
    if request_obj and getattr(request_obj, "client", None):
        client_ip = request_obj.client.host
    identifier = f"login:{client_ip}:{request.email}"
    if await is_blocked(identifier):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too many attempts")

    user, error = await AuthService.authenticate_user(
        db=db,
        email=request.email,
        password=request.password,
    )

    if error:
        await record_failed_attempt(identifier)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
        )

    await reset_attempts(identifier)

    tokens = AuthService.generate_tokens(user.id)
    return {
        "user": UserResponse.model_validate(user),
        "tokens": TokenResponse(**tokens),
    }


@router.post("/telegram/login", response_model=dict)
async def telegram_login(request_obj: Request, db: AsyncSession = Depends(get_db_session)) -> dict:
    """
    Accept raw Telegram init data (as sent by the WebApp). This endpoint is tolerant
    to both the raw Telegram parameter names (id, username, auth_date, hash, etc.)
    and our internal field names (telegram_id, telegram_username). We parse and
    verify the signature using the configured bot token, then map values to the
    AuthService call.
    """
    try:
        raw = await request_obj.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    # Accept input either as a single 'init_data' string (legacy) or as an object
    telegram_payload = {}
    if isinstance(raw, dict) and raw.get('init_data') and isinstance(raw.get('init_data'), str):
        # If frontend sent a raw init_data string, parse it into dict
        from urllib.parse import parse_qs
        parsed = parse_qs(raw.get('init_data'))
        # parse_qs returns lists for each key; normalize to single values
        telegram_payload = {k: v[0] for k, v in parsed.items()}
    elif isinstance(raw, dict):
        telegram_payload = raw
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported Telegram payload format")

    # Normalize field names (allow both 'id' and 'telegram_id', 'username' and 'telegram_username')
    data_for_verification = dict(telegram_payload)  # copy

    if not verify_telegram_data(data_for_verification):
        logger.warning(
            f"[AUTH] Telegram login failed - signature verification failed | "
            f"telegram_id={data_for_verification.get('telegram_id') or data_for_verification.get('id')} | "
            f"hash_present={bool(data_for_verification.get('hash'))} | "
            f"auth_date={data_for_verification.get('auth_date')}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram data verification failed",
        )

    # Map fields for AuthService
    telegram_id = int(telegram_payload.get('telegram_id') or telegram_payload.get('id'))
    telegram_username = telegram_payload.get('telegram_username') or telegram_payload.get('username') or ''
    first_name = telegram_payload.get('first_name')
    last_name = telegram_payload.get('last_name')

    user, error = await AuthService.authenticate_telegram(
        db=db,
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        first_name=first_name,
        last_name=last_name,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    tokens = AuthService.generate_tokens(user.id)
    return {
        "user": UserResponse.model_validate(user),
        "tokens": TokenResponse(**tokens),
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    access_token, error = await AuthService.refresh_access_token(db, request.refresh_token)

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,
        token_type="bearer",
        expires_in=24 * 3600,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_route(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/profile", response_model=dict, tags=["user"])
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    
    Returns user data including avatar URL for display on frontend.
    Used by web app to fetch user profile information.
    """
    return {
        "success": True,
        "data": UserResponse.model_validate(current_user),
        "message": "User profile retrieved successfully"
    }
