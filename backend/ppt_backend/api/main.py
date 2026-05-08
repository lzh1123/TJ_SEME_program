from __future__ import annotations

from fastapi import FastAPI

from ..container import build_presentation_service
from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="AI PPT Generator Backend", version="0.1.0")
    app.state.presentation_service = build_presentation_service()
    app.include_router(router)
    return app


app = create_app()

