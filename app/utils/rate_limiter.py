import logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis = None


async def _get_redis_client():
    global _redis
    if _redis is None:
        try:
            import redis.asyncio as redis
            _redis = redis.from_url(settings.redis_url, decode_responses=True)
        except Exception as e:
            logger.error(f"Failed to create redis client: {e}")
            raise
    return _redis


async def record_failed_attempt(key: str) -> int:
    """
    Record a failed login attempt.
    
    Args:
        key: Unique identifier for the failed attempt (e.g., email or IP)
    
    Returns:
        Attempt count; if Redis is down, returns high value to trigger blocking
    
    Important: Returns settings.login_max_attempts to trigger rate limiting
    if Redis connection fails (fail-safe behavior).
    """
    r = await _get_redis_client()
    try:
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, settings.login_block_minutes * 60)
        return int(count)
    except Exception as e:
        logger.error(
            f"Redis record_failed_attempt error: {e}. "
            f"Returning high count to trigger rate limiting (fail-safe)",
            exc_info=True
        )
        # Fail-safe: return high count to trigger blocking
        return settings.login_max_attempts


async def is_blocked(key: str) -> bool:
    """
    Check if a user/IP is blocked due to too many failed attempts.
    
    Returns:
        True if blocked or Redis is unavailable (fail-safe), False otherwise
    
    Note: Returns True on Redis error to prevent bypass during outages.
    """
    r = await _get_redis_client()
    try:
        val = await r.get(key)
        if val is None:
            return False
        return int(val) >= settings.login_max_attempts
    except Exception as e:
        logger.error(
            f"Redis is_blocked error: {e}. "
            f"Returning True to block (fail-safe during Redis outage)",
            exc_info=True
        )
        # Fail-safe: block if Redis is down
        return True


async def reset_attempts(key: str):
    r = await _get_redis_client()
    try:
        await r.delete(key)
    except Exception as e:
        logger.error(f"Redis reset_attempts error: {e}")


async def is_rate_limited(
    key: str,
    max_requests: int = None,
    window_seconds: int = None
) -> bool:
    """
    Check if a request exceeds rate limit.
    
    Args:
        key: Unique identifier (e.g., IP address or user ID)
        max_requests: Maximum requests allowed (defaults to config)
        window_seconds: Time window in seconds (defaults to config)
    
    Returns:
        True if rate limited or Redis is unavailable (fail-safe), False otherwise
    
    Note: Returns True on Redis error to prevent abuse during outages.
    """
    if max_requests is None:
        max_requests = settings.api_rate_limit
    if window_seconds is None:
        window_seconds = settings.api_rate_limit_window
    
    r = await _get_redis_client()
    try:
        current = await r.incr(key)
        if current == 1:
            await r.expire(key, window_seconds)
        return current > max_requests
    except Exception as e:
        logger.error(
            f"Redis is_rate_limited error: {e}. "
            f"Returning True to rate limit (fail-safe during Redis outage)",
            exc_info=True
        )
        # Fail-safe: rate limit if Redis is down
        return True

