import logging
from typing import Optional
from app.config import get_settings
logger = logging.getLogger(__name__)
settings = get_settings()
_redis = None
_redis_available = None
async def _get_redis_client():
    global _redis, _redis_available
    if _redis_available is not None:
        return _redis
    if _redis is None:
        try:
            import redis.asyncio as redis
            _redis = redis.from_url(settings.redis_url, decode_responses=True)
            await _redis.ping()
            _redis_available = True
            logger.info("Redis connection successful")
        except Exception as e:
            logger.warning(f"Redis unavailable (using in-memory fallback): {e}")
            _redis_available = False
            _redis = None
    return _redis
async def record_failed_attempt(key: str) -> int:
    r = await _get_redis_client()
    if not r:
        logger.debug(f"Redis unavailable - rate limiting disabled for {key}")
        return 0
    try:
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, settings.login_block_minutes * 60)
        return int(count)
    except Exception as e:
        logger.warning(f"Redis error recording attempt: {e}")
        return 0
async def is_blocked(key: str) -> bool:
    r = await _get_redis_client()
    if not r:
        logger.debug(f"Redis unavailable - rate limiting disabled, allowing {key}")
        return False
    try:
        val = await r.get(key)
        if val is None:
            return False
        return int(val) >= settings.login_max_attempts
    except Exception as e:
        logger.warning(f"Redis is_blocked error: {e}, allowing request")
        return False
async def reset_attempts(key: str):
    r = await _get_redis_client()
    if not r:
        return
    try:
        await r.delete(key)
    except Exception as e:
        logger.warning(f"Redis reset error: {e}")
async def is_rate_limited(
    key: str,
    max_requests: int = None,
    window_seconds: int = None
) -> bool:
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
        return True
