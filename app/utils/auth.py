"""
TELEGRAM-ONLY AUTHENTICATION (Stateless)
=========================================

This module is deprecated - all JWT/Bearer token logic has been removed.

The system now uses only Telegram WebApp initData verification:
- Every request can include Telegram initData in headers or body
- No persistent user sessions
- No Bearer tokens
- No refresh tokens

For authentication details, see:
- app.routers.telegram_auth_router (POST /api/auth/telegram/login)
- app.routers.unified_auth_router (full Telegram auth flow)
"""

import logging

logger = logging.getLogger(__name__)

# ============================================================================
# DEPRECATED: All functions below are no longer used
# Kept for backward compatibility only
# ============================================================================

async def get_current_user(*args, **kwargs):
    """
    ❌ DEPRECATED - JWT tokens removed
    
    This function is no longer used. Use Telegram authentication instead.
    
    See: app.routers.telegram_auth_router.py
    """
    raise NotImplementedError(
        "JWT authentication has been removed. Use Telegram WebApp initData instead. "
        "See /api/v1/auth/telegram/login endpoint."
    )


async def get_current_user_optional(*args, **kwargs):
    """
    ❌ DEPRECATED - JWT tokens removed
    
    This function is no longer used. Use Telegram authentication instead.
    """
    raise NotImplementedError(
        "JWT authentication has been removed. Use Telegram WebApp initData instead."
    )

