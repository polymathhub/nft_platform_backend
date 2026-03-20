import logging
import anyio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.config import get_settings
logger = logging.getLogger(__name__)
settings = get_settings()
class RequestBodyCachingMiddleware(BaseHTTPMiddleware):
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
        if request.url.path.startswith("/webapp"):
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        else:
            response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://telegram.org https://*.telegram.org; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self' https: https://*.telegram.org; "
            "frame-ancestors 'self' https://*.telegram.org; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        if request.url.path.startswith("/api/"):
            if request.method == "GET":
                # No caching for API GET requests - always fetch fresh data
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            else:
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
        return response
class RelaxedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if request.url.path.startswith("/webapp"):
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        else:
            response.headers["X-Frame-Options"] = "ALLOW-FROM https://telegram.org"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.require_https and not settings.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        csp = (
            "default-src 'self' https:; "
            "script-src 'self' 'unsafe-inline' https://*.telegram.org https://telegram.org https://unpkg.com https://cdn.jsdelivr.net https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "connect-src 'self' https: https://*.telegram.org; "
            "frame-ancestors 'self' https://*.telegram.org; "
            "base-uri 'self'; form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        # No aggressive caching for API endpoints - ensure fresh data always
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
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
class DirectoryListingBlockMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.startswith("/webapp/static"):
            path = request.url.path
            if path.endswith("/"):
                logger.warning(f"Blocked directory listing attempt on {path}")
                return JSONResponse(
                    content={"detail": "Not found"},
                    status_code=404
                )
        response = await call_next(request)
        return response
