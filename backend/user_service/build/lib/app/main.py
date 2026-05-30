from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes.auth import router as auth_router
from app.core.config import get_settings
from app.core.middleware import HSTSMiddleware, HTTPSRedirectMiddleware, ProxyHeadersMiddleware
from app.models import auth as auth_models  # noqa: F401
from app.models import user as user_models  # noqa: F401


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Auth Backend", version="0.1.0")
    app.add_middleware(ProxyHeadersMiddleware)
    app.add_middleware(HTTPSRedirectMiddleware)
    if settings.allowed_host_list and settings.allowed_host_list != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_host_list)
    app.add_middleware(HSTSMiddleware)
    app.include_router(auth_router, prefix="/auth", tags=["auth"])

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
