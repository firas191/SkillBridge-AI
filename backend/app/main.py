"""SkillBridge AI — FastAPI application entrypoint.

Run (development):
    uvicorn app.main:app --reload --app-dir backend
or from the backend/ directory:
    uvicorn app.main:app --reload

Interactive API docs are served at /docs once running.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.routes import (
    candidates,
    documents,
    health,
    interview,
    jobs,
    learning,
    matching,
)
from app.core.config import get_settings
from app.core.llm import LLMCallError, LLMNotConfiguredError
from app.core.logging import configure_logging, get_logger
from app.db.session import init_db

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger("skillbridge")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    log.info(
        "SkillBridge AI %s started | provider=%s model=%s",
        __version__,
        settings.llm_provider,
        settings.active_chat_model,
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="SkillBridge AI",
        version=__version__,
        description=(
            "Explainable, skill-based education & recruitment copilot. "
            "Foundation module: structured skill extraction + match engine."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(LLMCallError)
    async def _llm_call_error(_: Request, exc: LLMCallError) -> JSONResponse:
        log.warning("LLM call error: %s", exc)
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(LLMNotConfiguredError)
    async def _llm_not_configured(_: Request, exc: LLMNotConfiguredError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(candidates.router)
    app.include_router(jobs.router)
    app.include_router(matching.router)
    app.include_router(learning.router)
    app.include_router(interview.router)

    @app.get("/", tags=["system"])
    def root() -> dict:
        return {
            "name": "SkillBridge AI",
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
