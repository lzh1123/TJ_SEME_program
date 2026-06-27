from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..container import build_presentation_service
from .auth_routes import router as auth_router
from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Slideon - AI PPT Generator", version="0.2.0")

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.presentation_service = build_presentation_service()
    app.include_router(auth_router)
    app.include_router(router)
    return app


app = create_app()

