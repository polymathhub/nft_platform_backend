# ============================================================================
# SECURITY AUTH MODULE - Forwarding to Telegram Implementation
# ============================================================================
# This module forwards to the correct Telegram authentication implementation.
# All routers should import from app.utils.telegram_auth_dependency instead.
# This file is kept for backward compatibility only.

from app.utils.telegram_auth_dependency import get_current_user, get_current_user_optional

__all__ = ["get_current_user", "get_current_user_optional"]
