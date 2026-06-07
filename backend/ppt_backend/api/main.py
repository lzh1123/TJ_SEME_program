from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..container import build_presentation_service
from .routes import router

# Configure logging so RAG diagnostics are visible
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
# Keep noisy libs quiet
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("pymilvus").setLevel(logging.WARNING)

# ── Concurrency limiter ──
# Prevent thread pool exhaustion by limiting in-flight LLM generation requests
_MAX_CONCURRENT_GENERATIONS = 3
_semaphore: asyncio.Semaphore | None = None


def create_app() -> FastAPI:
    global _semaphore
    _semaphore = asyncio.Semaphore(_MAX_CONCURRENT_GENERATIONS)

    app = FastAPI(title="AI PPT Generator Backend", version="0.1.0")

    # 配置 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有方法
        allow_headers=["*"],  # 允许所有头
    )

    # Concurrency limiter middleware — applied only to heavy endpoints
    @app.middleware("http")
    async def concurrency_middleware(request: Request, call_next):
        # Only limit generation endpoints
        heavy_paths = {"/dsl", "/presentations"}
        is_heavy = any(request.url.path.endswith(p) or request.url.path.rstrip("/").endswith(p) for p in heavy_paths)
        # Also match /presentations/{id}/regenerate
        is_heavy = is_heavy or "/regenerate" in request.url.path

        if not is_heavy or request.method == "GET":
            return await call_next(request)

        # Wait up to 60s for a generation slot, else return 503
        try:
            await asyncio.wait_for(_semaphore.acquire(), timeout=60.0)
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=503,
                content={"detail": "Server busy — too many concurrent generation requests. Please wait and retry.", "error_type": "server_busy"},
            )

        try:
            response = await call_next(request)
            return response
        finally:
            _semaphore.release()

    app.state.presentation_service = build_presentation_service()
    app.include_router(router)

    # Start import task queue worker
    from ..services.rag.task_queue import get_import_queue
    import_queue = get_import_queue()

    @app.on_event("startup")
    async def start_import_worker():
        await import_queue.start()

    @app.on_event("shutdown")
    async def stop_import_worker():
        await import_queue.stop()

    return app


app = create_app()

