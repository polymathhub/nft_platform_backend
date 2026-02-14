from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.config import get_settings

settings = get_settings()


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