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
async def telegram_login(
    request: TelegramLoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    telegram_data = request.model_dump()
    if not verify_telegram_data(telegram_data):
        logger.warning(f"Invalid Telegram login attempt - signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram data verification failed",
        )
    
    user, error = await AuthService.authenticate_telegram(
        db=db,
        telegram_id=request.telegram_id,
        telegram_username=request.telegram_username,
        first_name=request.first_name,
        last_name=request.last_name,
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
