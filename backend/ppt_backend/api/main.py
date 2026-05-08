from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..container import build_presentation_service
from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="AI PPT Generator Backend", version="0.1.0")
    
    # 配置 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有方法
        allow_headers=["*"],  # 允许所有头
    )
    
    app.state.presentation_service = build_presentation_service()
    app.include_router(router)
    return app


app = create_app()

