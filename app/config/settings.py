"""Impostazioni dell'applicazione, lette da variabili d'ambiente / file .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    agency_config_path: str = "config/agency.example.yaml"
    database_url: str = "sqlite:///./fluxassist.db"

    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_api_version: str = "v21.0"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    llm_provider: str = "gemini"  # "gemini" | "fallback"

    google_calendar_credentials: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
