from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.core.config import get_settings


class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if settings.trust_proxy_headers:
            proto = request.headers.get("x-forwarded-proto")
            if proto:
                request.scope["scheme"] = proto.split(",")[0].strip()
        return await call_next(request)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        proto = request.headers.get("x-forwarded-proto")
        scheme = proto.split(",")[0].strip() if proto else request.url.scheme
        if settings.force_https and scheme != "https":
            url = request.url.replace(scheme="https")
            return RedirectResponse(str(url), status_code=307)
        return await call_next(request)


class HSTSMiddleware(BaseHTTPMiddleware):
    def _value(self) -> str:
        settings = get_settings()
        parts = [f"max-age={settings.hsts_max_age}"]
        if settings.hsts_include_subdomains:
            parts.append("includeSubDomains")
        if settings.hsts_preload:
            parts.append("preload")
        return "; ".join(parts)

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        response: Response = await call_next(request)
        proto = request.headers.get("x-forwarded-proto")
        scheme = proto.split(",")[0].strip() if proto else request.url.scheme
        if settings.hsts_enabled and scheme == "https":
            response.headers["Strict-Transport-Security"] = self._value()
        return response
