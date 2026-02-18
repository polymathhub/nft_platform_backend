import logging
import anyio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RequestPathValidationMiddleware(BaseHTTPMiddleware):
    """Validate and reject requests with suspicious path patterns."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        
        # Skip validation for safe endpoints
        safe_prefixes = ["/web-app/", "/api/v1/telegram/web-app/", "/static/", "/.well-known/"]
        if any(path.startswith(prefix) for prefix in safe_prefixes):
            # For internal endpoints, only check for obvious code injection
            if any(pattern in path for pattern in ["eval(", "exec(", "exec%20"]):
                logger.warning(f"BLOCKED: Code injection attempt | Path: {path}")
                return JSONResponse(status_code=400, content={"detail": "Invalid request"})
            # Allow the request
            return await call_next(request)
        
        # Suspicious patterns that indicate potential attacks
        dangerous_patterns = [
            ("https://", "URL in path"),
            ("http://", "URL in path"),
            ("%3A%2F%2F", "Encoded URL in path"),
            ("../../", "Path traversal"),
            ("..%2F", "Encoded path traversal"),
            ("%00", "Null byte injection"),
            ("eval(", "Code injection"),
            ("exec(", "Code injection"),
            ("<script>", "XSS attempt"),
            ("<iframe>", "XSS attempt"),
            ("cmd=", "Command injection"),
            ("exec%20", "Code injection"),
        ]
        
        # Check for suspicious patterns
        for pattern, threat_type in dangerous_patterns:
            if pattern in path:
                logger.warning(
                    f"BLOCKED: {threat_type} in path | "
                    f"Method: {request.method} | "
                    f"Path: {path} | "
                    f"Client: {request.client.host if request.client else 'unknown'}"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Invalid request path",
                        "status_code": 400,
                    }
                )
        
        # Allow request through
        response = await call_next(request)
        return response


class RequestBodyCachingMiddleware(BaseHTTPMiddleware):
    """Cache request body early to prevent stream exhaustion errors."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                request.state.body = body
            except anyio.EndOfStream:
                logger.warning("Client disconnected before sending body")
                return Response(content=b"", status_code=499)
            except anyio.WouldBlock:
                logger.warning("Stream operation would block")
                return Response(content=b"", status_code=503)
            except Exception as e:
                logger.error(f"Error reading request body: {e}")
                request.state.body = b""
        
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # Intelligent caching based on request type and path
        if request.url.path.startswith("/api/"):
            # Allow caching for GET requests to safe endpoints (60 seconds)
            if request.method == "GET":
                # Cache dashboard data and read-only endpoints
                if any(path in request.url.path for path in [
                    "/web-app/dashboard-data",
                    "/web-app/init",
                    "/health",
                    "/nft/",
                    "/wallet/",
                    "/marketplace/listings"
                ]):
                    response.headers["Cache-Control"] = "public, max-age=60"
                    response.headers["ETag"] = getattr(response, '_etag', None) or ""
            else:
                # Disable caching for mutations (POST, PUT, PATCH, DELETE)
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
        
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.max_request_size:
                return Response(
                    content={"error": "Request body too large"},
                    status_code=413,
                    media_type="application/json"
                )
        
        return await call_next(request)


class HTTPSEnforcementMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if settings.require_https and not settings.debug:
            if request.url.scheme != "https":
                forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
                if forwarded_proto != "https":
                    return Response(
                        content={"error": "HTTPS required"},
                        status_code=403,
                        media_type="application/json"
                    )
        
        return await call_next(request)