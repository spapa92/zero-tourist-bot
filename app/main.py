"""Entrypoint FastAPI."""

from __future__ import annotations

from fastapi import FastAPI

from app.config.settings import get_settings
from app.deps import build_container
from app.whatsapp.webhooks import build_webhook_router


def create_app() -> FastAPI:
    settings = get_settings()
    container = build_container(settings)

    app = FastAPI(title="FluxAssist")
    app.state.settings = settings
    app.state.container = container
    # Viene esposto solo il webhook del canale attivo (Meta oppure Twilio).
    app.include_router(build_webhook_router(settings.whatsapp_provider))

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "whatsapp_provider": container.whatsapp.provider,
            "whatsapp_configured": container.whatsapp.is_configured(),
        }

    return app


app = create_app()
