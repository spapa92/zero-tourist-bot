"""Impostazioni dell'applicazione, lette da variabili d'ambiente / file .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WHATSAPP_PROVIDERS = ("meta", "twilio")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    agency_config_path: str = "config/agency.example.yaml"
    database_url: str = "sqlite:///./fluxassist.db"

    # Canale WhatsApp attivo: "meta" (Cloud API) oppure "twilio". Uno alla volta.
    whatsapp_provider: str = "meta"

    # ── Provider: Meta WhatsApp Business Cloud API ──
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_api_version: str = "v21.0"

    # ── Provider: Twilio ──
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""
    twilio_messaging_service_sid: str = ""
    twilio_content_sid_reopener: str = ""
    twilio_content_sid_reminder: str = ""
    twilio_webhook_url: str = ""
    twilio_validate_signature: bool = True

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    llm_provider: str = "gemini"  # "gemini" | "fallback"

    google_calendar_credentials: str = ""

    # ── Dashboard lead (Basic Auth) ──
    dashboard_username: str = ""
    dashboard_password: str = ""

    @field_validator("whatsapp_provider")
    @classmethod
    def _validate_whatsapp_provider(cls, value: str) -> str:
        provider = (value or "").strip().lower()
        if provider not in WHATSAPP_PROVIDERS:
            raise ValueError(
                f"WHATSAPP_PROVIDER '{value}' non supportato: "
                f"usa uno tra {', '.join(WHATSAPP_PROVIDERS)}."
            )
        return provider


@lru_cache
def get_settings() -> Settings:
    return Settings()
