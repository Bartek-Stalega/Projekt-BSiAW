import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings
from app.security import generate_token

settings = get_settings()
logger = logging.getLogger("secforum.access")

# Aplikacja nie uzywa zewnetrznych CDN-ow ani inline JS, wiec polityka moze byc waska.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "img-src 'self' data:; "
    "style-src 'self'; "
    "script-src 'self'; "
    "object-src 'none'; "
    "base-uri 'none'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Naglowki bezpieczenstwa.

    Docelowo (L7) czesc z nich ustawi tez Application Gateway / Front Door -
    trzymanie ich w aplikacji daje ochrone niezaleznie od warstwy brzegowej.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if settings.cookie_secure:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


class CsrfCookieMiddleware(BaseHTTPMiddleware):
    """Zapewnia obecnosc ciasteczka CSRF uzywanego w formularzach."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        token = request.cookies.get(settings.csrf_cookie_name)
        issue_cookie = token is None
        if issue_cookie:
            token = generate_token(16)
        request.state.csrf_token = token

        response = await call_next(request)
        if issue_cookie:
            response.set_cookie(
                settings.csrf_cookie_name,
                token,
                httponly=True,
                secure=settings.cookie_secure,
                samesite="lax",
                path="/",
            )
        return response


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Log dostepowy z identyfikatorem korelacji (przyda sie w Azure Monitor)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            'request_id=%s method=%s path="%s" status=%s duration_ms=%.1f',
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
