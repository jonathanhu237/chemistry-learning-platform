from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _getenv(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _get_int(name: str, default: int) -> int:
    value = _getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


def _get_bool(name: str, default: bool) -> bool:
    value = _getenv(name)
    if not value:
        return default
    normalized = value.lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be a boolean")


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_env: str = "development"
    data_backend: str = "json"
    database_url: str = "postgresql+psycopg://chemistry:chemistry@localhost:5432/chemistry_exam"
    run_db_check_on_startup: bool = False
    media_root: Path = ROOT / "data" / "media"
    api_public_base_url: str = "http://127.0.0.1:8000"
    frontend_allowed_origins: tuple[str, ...] = ("*",)
    auth_secret_key: str = "dev-only-secret"
    access_token_expire_minutes: int = 720
    max_media_upload_mb: int = 1024
    agent_llm_provider: str = "disabled"
    agent_llm_base_url: str = ""
    agent_llm_api_key: str = ""
    agent_llm_model: str = ""
    admin_web_dist: Path = ROOT / "apps" / "admin-web" / "dist"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    def validate_startup(self) -> None:
        errors: list[str] = []
        if self.data_backend not in {"json", "postgres"}:
            errors.append("DATA_BACKEND must be json or postgres")
        if self.is_production:
            if self.data_backend != "postgres":
                errors.append("DATA_BACKEND must be postgres in production")
            if not _getenv("DATABASE_URL"):
                errors.append("DATABASE_URL is required in production")
            if not _getenv("MEDIA_ROOT"):
                errors.append("MEDIA_ROOT is required in production")
            if not _getenv("API_PUBLIC_BASE_URL"):
                errors.append("API_PUBLIC_BASE_URL is required in production")
            if not _getenv("AUTH_SECRET_KEY") or self.auth_secret_key in {"", "dev-only-secret", "dev-only-change-me"}:
                errors.append("AUTH_SECRET_KEY must be set to a non-development value in production")
            if not _getenv("AGENT_LLM_PROVIDER"):
                errors.append("AGENT_LLM_PROVIDER must be explicit in production, use disabled when no LLM is configured")
            if self.agent_llm_provider and self.agent_llm_provider != "disabled":
                if not self.agent_llm_api_key:
                    errors.append("AGENT_LLM_API_KEY is required when AGENT_LLM_PROVIDER is enabled")
                if not self.agent_llm_model:
                    errors.append("AGENT_LLM_MODEL is required when AGENT_LLM_PROVIDER is enabled")
        if errors:
            raise RuntimeError("Invalid production configuration: " + "; ".join(errors))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    app_env = _getenv("CHEMISTRY_APP_ENV", _getenv("APP_ENV", "development"))
    origins = _split_csv(_getenv("FRONTEND_ALLOWED_ORIGINS", "*"))
    return Settings(
        app_env=app_env,
        data_backend=_getenv("DATA_BACKEND", Settings.data_backend).lower(),
        database_url=_getenv("DATABASE_URL", Settings.database_url),
        run_db_check_on_startup=_get_bool("RUN_DB_CHECK_ON_STARTUP", app_env.lower() in {"production", "prod"}),
        media_root=Path(_getenv("MEDIA_ROOT", str(Settings.media_root))),
        api_public_base_url=_getenv("API_PUBLIC_BASE_URL", Settings.api_public_base_url).rstrip("/"),
        frontend_allowed_origins=tuple(origins or ["*"]),
        auth_secret_key=_getenv("AUTH_SECRET_KEY", Settings.auth_secret_key),
        access_token_expire_minutes=_get_int("ACCESS_TOKEN_EXPIRE_MINUTES", Settings.access_token_expire_minutes),
        max_media_upload_mb=_get_int("MAX_MEDIA_UPLOAD_MB", Settings.max_media_upload_mb),
        agent_llm_provider=_getenv("AGENT_LLM_PROVIDER", Settings.agent_llm_provider).lower(),
        agent_llm_base_url=_getenv("AGENT_LLM_BASE_URL"),
        agent_llm_api_key=_getenv("AGENT_LLM_API_KEY"),
        agent_llm_model=_getenv("AGENT_LLM_MODEL"),
        admin_web_dist=Path(_getenv("ADMIN_WEB_DIST", str(Settings.admin_web_dist))),
    )
