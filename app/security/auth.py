"""
Authentication dependencies for FastAPI.
Provides get_current_user for route protection.
"""

from app.utils.auth import get_current_user

__all__ = ["get_current_user"]
