import logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis = None
_redis_available = None  # Track if Redis is available


async def _get_redis_client():
    """Get Redis client, gracefully handle if Redis is unavailable."""
    global _redis, _redis_available
    
    if _redis_available is not None:
        return _redis  # Use cached availability status
    
    if _redis is None:
        try:
            import redis.asyncio as redis
            _redis = redis.from_url(settings.redis_url, decode_responses=True)
            # Test connection
            await _redis.ping()
            _redis_available = True
            logger.info("Redis connection successful")
        except Exception as e:
            logger.warning(f"Redis unavailable (using in-memory fallback): {e}")
            _redis_available = False
            _redis = None
    return _redis


async def record_failed_attempt(key: str) -> int:
    """
    Record a failed login attempt.
    
    Args:
        key: Unique identifier for the failed attempt (e.g., email or IP)
    
    Returns:
        Attempt count; if Redis is down, returns 0 (no rate limiting in dev)
    """
    r = await _get_redis_client()
    if not r:
        logger.debug(f"Redis unavailable - rate limiting disabled for {key}")
        return 0  # No rate limiting if Redis is down
    
    try:
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, settings.login_block_minutes * 60)
        return int(count)
    except Exception as e:
        logger.warning(f"Redis error recording attempt: {e}")
        return 0  # No rate limiting on Redis error


async def is_blocked(key: str) -> bool:
    """
    Check if a user/IP is blocked due to too many failed attempts.
    
    Returns:
        True if blocked, False if Redis is unavailable or not blocked
    
    Note: If Redis is unavailable, returns False (dev mode)
    """
    r = await _get_redis_client()
    if not r:
        logger.debug(f"Redis unavailable - rate limiting disabled, allowing {key}")
        return False  # No rate limiting if Redis is down
    
    try:
        val = await r.get(key)
        if val is None:
            return False
        return int(val) >= settings.login_max_attempts
    except Exception as e:
        logger.warning(f"Redis is_blocked error: {e}, allowing request")
        return False  # Allow on error (dev mode)


async def reset_attempts(key: str):
    """Reset failed attempts for a key."""
    r = await _get_redis_client()
    if not r:
        return  # No-op if Redis is unavailable
    
    try:
        await r.delete(key)
    except Exception as e:
        logger.warning(f"Redis reset error: {e}")


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

