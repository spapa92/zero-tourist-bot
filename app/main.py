"""Entrypoint FastAPI."""

from __future__ import annotations

from fastapi import FastAPI

from app.config.settings import get_settings
from app.deps import build_container
from app.whatsapp.webhook import router as webhook_router


def create_app() -> FastAPI:
    settings = get_settings()
    container = build_container(settings)

    app = FastAPI(title="FluxAssist")
    app.state.settings = settings
    app.state.container = container
    app.include_router(webhook_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
