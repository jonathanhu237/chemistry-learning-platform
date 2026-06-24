from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


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


def _get_float(name: str, default: float) -> float:
    value = _getenv(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a float") from exc


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
    database_url: str = "postgresql+psycopg://chemistry:chemistry@127.0.0.1:15432/chemistry_exam"
    run_db_check_on_startup: bool = False
    media_root: Path = ROOT / "data" / "media"
    api_public_base_url: str = "http://127.0.0.1:8000"
    frontend_allowed_origins: tuple[str, ...] = ("*",)
    tus_upload_dir: str = "tus"
    tus_public_endpoint: str = ""
    video_worker_poll_seconds: int = 5
    video_worker_id: str = "local-video-worker"
    video_learning_max_width: int = 1280
    video_learning_crf: int = 24
    video_learning_max_fps: int = 30
    video_learning_transcode_threshold_mb: int = 300
    video_similarity_command: str = ""
    video_similarity_compare_command: str = ""
    video_similarity_algorithm: str = "external-video-similarity"
    video_similarity_threshold: float = 0.86
    auth_secret_key: str = "dev-only-secret"
    access_token_expire_minutes: int = 720
    web_admin_access_token: str = ""
    student_preview_app_base_url: str = "http://222.200.189.249:15173"
    student_preview_allowed_origins: tuple[str, ...] = (
        "http://222.200.189.249:15173",
        "http://127.0.0.1:15173",
        "http://localhost:15173",
    )
    student_preview_ticket_expire_minutes: int = 10
    student_preview_session_expire_minutes: int = 240
    max_media_upload_mb: int = 1024
    agent_llm_provider: str = "disabled"
    agent_llm_base_url: str = ""
    agent_llm_api_key: str = ""
    agent_llm_model: str = ""
    agent_reasoning_summary_enabled: bool = False
    agent_reasoning_summary_mode: str = "auto"
    agent_reasoning_effort: str = "low"
    rag_hybrid_bge_enabled: bool = False
    rag_query_generation_enabled: bool = True
    rag_bge_service_url: str = "http://bge-rag:8010"
    rag_bge_timeout_seconds: float = 8.0
    rag_keyword_top_k: int = 16
    rag_vector_top_k: int = 24
    rag_rerank_top_k: int = 9
    rag_final_top_k: int = 5
    catalog_point_evidence_auto_refresh: bool = False
    chemistry_rag_root: Path = Path("E:/chemistry-rag") if os.name == "nt" else Path("/chemistry-rag")
    textbook_rag_enabled: bool = False
    textbook_rag_elasticsearch_url: str = ""
    textbook_rag_elasticsearch_index: str = "canonical-rag-chunks-qwen-v1"
    textbook_rag_embedding_base_url: str = ""
    textbook_rag_embedding_api_key: str = ""
    textbook_rag_embedding_model: str = ""
    textbook_rag_embedding_dimension: int = 1024
    textbook_rag_rerank_base_url: str = ""
    textbook_rag_rerank_api_key: str = ""
    textbook_rag_rerank_model: str = ""
    textbook_rag_min_rerank_score: float = 0.0
    textbook_rag_timeout_seconds: float = 8.0
    video_library_search_enabled: bool = True
    video_library_search_backend: str = "local"
    video_library_search_url: str = ""
    video_library_search_index: str = "student-video-library"
    video_library_search_analyzer: str = "ik_max_word"
    video_library_search_bootstrap_index: bool = True
    video_library_search_timeout_seconds: float = 3.0
    video_library_search_local_fallback: bool = True
    video_library_search_require_es_in_production: bool = True
    teacher_catalog_search_enabled: bool = True
    teacher_catalog_search_backend: str = "elasticsearch"
    teacher_catalog_search_url: str = ""
    teacher_catalog_search_index: str = "teacher-catalog-admin-search"
    teacher_catalog_search_analyzer: str = "ik_max_word"
    teacher_catalog_search_timeout_seconds: float = 3.0
    teacher_catalog_search_local_fallback: bool = True

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    def validate_startup(self) -> None:
        errors: list[str] = []
        if self.data_backend not in {"json", "postgres"}:
            errors.append("DATA_BACKEND must be json or postgres")
        if self.video_library_search_backend not in {"local", "elasticsearch", "disabled"}:
            errors.append("VIDEO_LIBRARY_SEARCH_BACKEND must be local, elasticsearch, or disabled")
        if self.teacher_catalog_search_backend not in {"elasticsearch", "disabled"}:
            errors.append("TEACHER_CATALOG_SEARCH_BACKEND must be elasticsearch or disabled")
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
            if (
                not _getenv("WEB_ADMIN_ACCESS_TOKEN")
                or len(self.web_admin_access_token) < 32
                or self.web_admin_access_token.startswith("dev-only-")
            ):
                errors.append("WEB_ADMIN_ACCESS_TOKEN must be set to a long non-development value in production")
            if not _getenv("AGENT_LLM_PROVIDER"):
                errors.append("AGENT_LLM_PROVIDER must be explicit in production, use disabled when no LLM is configured")
            if self.agent_llm_provider and self.agent_llm_provider != "disabled":
                if not self.agent_llm_api_key:
                    errors.append("AGENT_LLM_API_KEY is required when AGENT_LLM_PROVIDER is enabled")
                if not self.agent_llm_model:
                    errors.append("AGENT_LLM_MODEL is required when AGENT_LLM_PROVIDER is enabled")
            if self.textbook_rag_enabled:
                if not self.textbook_rag_elasticsearch_url:
                    errors.append("TEXTBOOK_RAG_ELASTICSEARCH_URL is required when textbook RAG is enabled")
                if not self.textbook_rag_embedding_api_key:
                    errors.append("TEXTBOOK_RAG_EMBEDDING_API_KEY is required when textbook RAG is enabled")
                if not self.textbook_rag_embedding_model:
                    errors.append("TEXTBOOK_RAG_EMBEDDING_MODEL is required when textbook RAG is enabled")
                if not self.textbook_rag_rerank_api_key:
                    errors.append("TEXTBOOK_RAG_RERANK_API_KEY is required when textbook RAG is enabled")
                if not self.textbook_rag_rerank_model:
                    errors.append("TEXTBOOK_RAG_RERANK_MODEL is required when textbook RAG is enabled")
            if self.video_library_search_enabled and self.video_library_search_require_es_in_production:
                if self.video_library_search_backend != "elasticsearch":
                    errors.append("VIDEO_LIBRARY_SEARCH_BACKEND must be elasticsearch in production when video-library search is enabled")
                if not self.video_library_search_url:
                    errors.append("VIDEO_LIBRARY_SEARCH_URL is required in production when video-library search is enabled")
                if self.video_library_search_local_fallback:
                    errors.append("VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK must be false in production")
        if errors:
            raise RuntimeError("Invalid production configuration: " + "; ".join(errors))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    app_env = _getenv("CHEMISTRY_APP_ENV", _getenv("APP_ENV", "development"))
    origins = _split_csv(_getenv("FRONTEND_ALLOWED_ORIGINS", "*"))
    student_preview_app_base_url = _getenv(
        "STUDENT_PREVIEW_APP_BASE_URL",
        Settings.student_preview_app_base_url,
    ).rstrip("/")
    student_preview_allowed_origins = _split_csv(_getenv("STUDENT_PREVIEW_ALLOWED_ORIGINS"))
    if not student_preview_allowed_origins:
        student_preview_allowed_origins = [student_preview_app_base_url]
    return Settings(
        app_env=app_env,
        data_backend=_getenv("DATA_BACKEND", Settings.data_backend).lower(),
        database_url=_getenv("DATABASE_URL", Settings.database_url),
        run_db_check_on_startup=_get_bool("RUN_DB_CHECK_ON_STARTUP", app_env.lower() in {"production", "prod"}),
        media_root=Path(_getenv("MEDIA_ROOT", str(Settings.media_root))),
        api_public_base_url=_getenv("API_PUBLIC_BASE_URL", Settings.api_public_base_url).rstrip("/"),
        frontend_allowed_origins=tuple(origins or ["*"]),
        tus_upload_dir=_getenv("TUS_UPLOAD_DIR", Settings.tus_upload_dir),
        tus_public_endpoint=_getenv("TUS_PUBLIC_ENDPOINT", Settings.tus_public_endpoint).rstrip("/"),
        video_worker_poll_seconds=_get_int("VIDEO_WORKER_POLL_SECONDS", Settings.video_worker_poll_seconds),
        video_worker_id=_getenv("VIDEO_WORKER_ID", Settings.video_worker_id),
        video_learning_max_width=_get_int("VIDEO_LEARNING_MAX_WIDTH", Settings.video_learning_max_width),
        video_learning_crf=_get_int("VIDEO_LEARNING_CRF", Settings.video_learning_crf),
        video_learning_max_fps=_get_int("VIDEO_LEARNING_MAX_FPS", Settings.video_learning_max_fps),
        video_learning_transcode_threshold_mb=_get_int(
            "VIDEO_LEARNING_TRANSCODE_THRESHOLD_MB",
            Settings.video_learning_transcode_threshold_mb,
        ),
        video_similarity_command=_getenv("VIDEO_SIMILARITY_COMMAND", Settings.video_similarity_command),
        video_similarity_compare_command=_getenv(
            "VIDEO_SIMILARITY_COMPARE_COMMAND",
            Settings.video_similarity_compare_command,
        ),
        video_similarity_algorithm=_getenv("VIDEO_SIMILARITY_ALGORITHM", Settings.video_similarity_algorithm),
        video_similarity_threshold=_get_float("VIDEO_SIMILARITY_THRESHOLD", Settings.video_similarity_threshold),
        auth_secret_key=_getenv("AUTH_SECRET_KEY", Settings.auth_secret_key),
        access_token_expire_minutes=_get_int("ACCESS_TOKEN_EXPIRE_MINUTES", Settings.access_token_expire_minutes),
        web_admin_access_token=_getenv("WEB_ADMIN_ACCESS_TOKEN", Settings.web_admin_access_token),
        student_preview_app_base_url=student_preview_app_base_url,
        student_preview_allowed_origins=tuple(student_preview_allowed_origins),
        student_preview_ticket_expire_minutes=_get_int(
            "STUDENT_PREVIEW_TICKET_EXPIRE_MINUTES",
            Settings.student_preview_ticket_expire_minutes,
        ),
        student_preview_session_expire_minutes=_get_int(
            "STUDENT_PREVIEW_SESSION_EXPIRE_MINUTES",
            Settings.student_preview_session_expire_minutes,
        ),
        max_media_upload_mb=_get_int("MAX_MEDIA_UPLOAD_MB", Settings.max_media_upload_mb),
        agent_llm_provider=_getenv("AGENT_LLM_PROVIDER", Settings.agent_llm_provider).lower(),
        agent_llm_base_url=_getenv("AGENT_LLM_BASE_URL"),
        agent_llm_api_key=_getenv("AGENT_LLM_API_KEY"),
        agent_llm_model=_getenv("AGENT_LLM_MODEL"),
        agent_reasoning_summary_enabled=_get_bool(
            "AGENT_REASONING_SUMMARY_ENABLED",
            Settings.agent_reasoning_summary_enabled,
        ),
        agent_reasoning_summary_mode=_getenv(
            "AGENT_REASONING_SUMMARY_MODE",
            Settings.agent_reasoning_summary_mode,
        ).lower(),
        agent_reasoning_effort=_getenv(
            "AGENT_REASONING_EFFORT",
            Settings.agent_reasoning_effort,
        ).lower(),
        rag_hybrid_bge_enabled=_get_bool("RAG_HYBRID_BGE_ENABLED", Settings.rag_hybrid_bge_enabled),
        rag_query_generation_enabled=_get_bool("RAG_QUERY_GENERATION_ENABLED", Settings.rag_query_generation_enabled),
        rag_bge_service_url=_getenv("RAG_BGE_SERVICE_URL", Settings.rag_bge_service_url).rstrip("/"),
        rag_bge_timeout_seconds=_get_float("RAG_BGE_TIMEOUT_SECONDS", Settings.rag_bge_timeout_seconds),
        rag_keyword_top_k=_get_int("RAG_KEYWORD_TOP_K", Settings.rag_keyword_top_k),
        rag_vector_top_k=_get_int("RAG_VECTOR_TOP_K", Settings.rag_vector_top_k),
        rag_rerank_top_k=_get_int("RAG_RERANK_TOP_K", Settings.rag_rerank_top_k),
        rag_final_top_k=_get_int("RAG_FINAL_TOP_K", Settings.rag_final_top_k),
        catalog_point_evidence_auto_refresh=_get_bool(
            "CATALOG_POINT_EVIDENCE_AUTO_REFRESH",
            Settings.catalog_point_evidence_auto_refresh,
        ),
        chemistry_rag_root=Path(_getenv("CHEMISTRY_RAG_ROOT", str(Settings.chemistry_rag_root))),
        textbook_rag_enabled=_get_bool("TEXTBOOK_RAG_ENABLED", Settings.textbook_rag_enabled),
        textbook_rag_elasticsearch_url=_getenv("TEXTBOOK_RAG_ELASTICSEARCH_URL").rstrip("/"),
        textbook_rag_elasticsearch_index=_getenv(
            "TEXTBOOK_RAG_ELASTICSEARCH_INDEX",
            Settings.textbook_rag_elasticsearch_index,
        ),
        textbook_rag_embedding_base_url=_getenv("TEXTBOOK_RAG_EMBEDDING_BASE_URL").rstrip("/"),
        textbook_rag_embedding_api_key=_getenv("TEXTBOOK_RAG_EMBEDDING_API_KEY"),
        textbook_rag_embedding_model=_getenv("TEXTBOOK_RAG_EMBEDDING_MODEL"),
        textbook_rag_embedding_dimension=_get_int(
            "TEXTBOOK_RAG_EMBEDDING_DIMENSION",
            Settings.textbook_rag_embedding_dimension,
        ),
        textbook_rag_rerank_base_url=_getenv("TEXTBOOK_RAG_RERANK_BASE_URL").rstrip("/"),
        textbook_rag_rerank_api_key=_getenv("TEXTBOOK_RAG_RERANK_API_KEY"),
        textbook_rag_rerank_model=_getenv("TEXTBOOK_RAG_RERANK_MODEL"),
        textbook_rag_min_rerank_score=_get_float(
            "TEXTBOOK_RAG_MIN_RERANK_SCORE",
            Settings.textbook_rag_min_rerank_score,
        ),
        textbook_rag_timeout_seconds=_get_float(
            "TEXTBOOK_RAG_TIMEOUT_SECONDS",
            Settings.textbook_rag_timeout_seconds,
        ),
        video_library_search_enabled=_get_bool(
            "VIDEO_LIBRARY_SEARCH_ENABLED",
            Settings.video_library_search_enabled,
        ),
        video_library_search_backend=_getenv(
            "VIDEO_LIBRARY_SEARCH_BACKEND",
            Settings.video_library_search_backend,
        ).lower(),
        video_library_search_url=_getenv("VIDEO_LIBRARY_SEARCH_URL").rstrip("/"),
        video_library_search_index=_getenv(
            "VIDEO_LIBRARY_SEARCH_INDEX",
            Settings.video_library_search_index,
        ),
        video_library_search_analyzer=_getenv(
            "VIDEO_LIBRARY_SEARCH_ANALYZER",
            Settings.video_library_search_analyzer,
        ),
        video_library_search_bootstrap_index=_get_bool(
            "VIDEO_LIBRARY_SEARCH_BOOTSTRAP_INDEX",
            Settings.video_library_search_bootstrap_index,
        ),
        video_library_search_timeout_seconds=_get_float(
            "VIDEO_LIBRARY_SEARCH_TIMEOUT_SECONDS",
            Settings.video_library_search_timeout_seconds,
        ),
        video_library_search_local_fallback=_get_bool(
            "VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK",
            Settings.video_library_search_local_fallback,
        ),
        video_library_search_require_es_in_production=_get_bool(
            "VIDEO_LIBRARY_SEARCH_REQUIRE_ES_IN_PRODUCTION",
            Settings.video_library_search_require_es_in_production,
        ),
        teacher_catalog_search_enabled=_get_bool(
            "TEACHER_CATALOG_SEARCH_ENABLED",
            Settings.teacher_catalog_search_enabled,
        ),
        teacher_catalog_search_backend=_getenv(
            "TEACHER_CATALOG_SEARCH_BACKEND",
            Settings.teacher_catalog_search_backend,
        ).lower(),
        teacher_catalog_search_url=_getenv(
            "TEACHER_CATALOG_SEARCH_URL",
            _getenv("VIDEO_LIBRARY_SEARCH_URL", Settings.teacher_catalog_search_url),
        ).rstrip("/"),
        teacher_catalog_search_index=_getenv(
            "TEACHER_CATALOG_SEARCH_INDEX",
            Settings.teacher_catalog_search_index,
        ),
        teacher_catalog_search_analyzer=_getenv(
            "TEACHER_CATALOG_SEARCH_ANALYZER",
            Settings.teacher_catalog_search_analyzer,
        ),
        teacher_catalog_search_timeout_seconds=_get_float(
            "TEACHER_CATALOG_SEARCH_TIMEOUT_SECONDS",
            Settings.teacher_catalog_search_timeout_seconds,
        ),
        teacher_catalog_search_local_fallback=_get_bool(
            "TEACHER_CATALOG_SEARCH_LOCAL_FALLBACK",
            Settings.teacher_catalog_search_local_fallback,
        ),
    )
