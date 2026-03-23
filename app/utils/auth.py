"""Compatibility wrapper for Telegram-based authentication.

This module exposes `get_current_user` and `get_current_user_optional`
dependencies for existing routers. They delegate to the Telegram
stateless authentication dependency implemented in
`app.utils.telegram_auth_dependency`.

The goal is to ensure all imports of `app.utils.auth.get_current_user`
continue to work while the project is Telegram-native and stateless.
"""
from app.utils.telegram_auth_dependency import get_current_user, get_current_user_optional

__all__ = ["get_current_user", "get_current_user_optional"]

