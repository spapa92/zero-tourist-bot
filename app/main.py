"""Entrypoint FastAPI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from app.config.settings import get_settings
from app.dashboard.api import router as dashboard_router
from app.dashboard.auth import basic_auth_middleware
from app.dashboard.spa_static import SPAStaticFiles
from app.deps import build_container
from app.whatsapp.webhooks import build_webhook_router

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    settings = get_settings()
    container = build_container(settings)

    app = FastAPI(title="FluxAssist")
    app.state.settings = settings
    app.state.container = container
    # Viene esposto solo il webhook del canale attivo (Meta oppure Twilio).
    app.include_router(build_webhook_router(settings.whatsapp_provider))
    app.include_router(dashboard_router)

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "whatsapp_provider": container.whatsapp.provider,
            "whatsapp_configured": container.whatsapp.is_configured(),
        }

    # Protegge tutto tranne /webhook e /health (dashboard API + frontend statico).
    app.middleware("http")(basic_auth_middleware)

    # Frontend buildato (npm run build): assente in dev backend-only, il mount viene saltato.
    if FRONTEND_DIST.is_dir():
        app.mount("/", SPAStaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    return app


app = create_app()
