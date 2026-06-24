from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from server.app.infrastructure.settings import Settings, get_settings
from server.app.infrastructure.database import db_session

LEARNING_SETTINGS_KEY = "learning_behavior"
AI_CONFIGURATION_KEY = "ai_configuration"


class SmartAssessmentSettings(BaseModel):
    enabled: bool = True
    question_count: int = Field(default=10, ge=1, le=50)
    untested_ratio_percent: int = Field(default=20, ge=0, le=100)
    weak_tendency_percent: int = Field(default=70, ge=0, le=100)
    max_questions_per_experiment: int = Field(default=2, ge=1, le=10)
    weak_curve: float = Field(default=2.0, ge=0.5, le=4.0)
    weak_max_bonus: float = Field(default=9.0, ge=1.0, le=20.0)


class CustomAssessmentSettings(BaseModel):
    enabled: bool = True
    default_question_count: int = Field(default=10, ge=5, le=20)
    max_question_count: int = Field(default=20, ge=5, le=20)
    max_questions_per_experiment: int = Field(default=3, ge=1, le=10)


class AssessmentSettings(BaseModel):
    pretest_enabled: bool = True
    pretest_question_count: int = Field(default=8, ge=1, le=50)
    posttest_enabled: bool = True
    posttest_question_count: int = Field(default=8, ge=1, le=50)
    smart_assessment: SmartAssessmentSettings = Field(default_factory=SmartAssessmentSettings)
    custom_assessment: CustomAssessmentSettings = Field(default_factory=CustomAssessmentSettings)


class LearningFeatureSettings(BaseModel):
    ai_assistant_enabled: bool = True
    feedback_enabled: bool = True
    student_review_preview_enabled: bool = False


class LearningBehaviorSettings(BaseModel):
    assessment: AssessmentSettings = Field(default_factory=AssessmentSettings)
    learning_features: LearningFeatureSettings = Field(default_factory=LearningFeatureSettings)


class AIEnabledFeatureScopes(BaseModel):
    rag_access_enabled: bool = True
    student_ai_assistant: bool = True
    student_learning_analytics: bool = True
    question_bank_assistant: bool = True
    teacher_learning_analytics: bool = True


class AIUsageBucket(BaseModel):
    bucket: str
    request_count: int = 0
    error_count: int = 0


class AIUsageTrend(BaseModel):
    range: str
    bucket_unit: str
    buckets: list[AIUsageBucket] = Field(default_factory=list)


class AILastRequestSummary(BaseModel):
    called_at: datetime
    channel: str
    status: str


class StudentAIPolicyOutcomeSummary(BaseModel):
    mode: str
    label: str
    count: int = 0


class StudentAIPolicyStatus(BaseModel):
    active: bool = True
    version: str = "student-ai-policy-v1"
    model: str = ""
    coverage: list[str] = Field(default_factory=list)
    recent_decision_count: int = 0
    invalid_decision_count: int = 0
    outcomes: list[StudentAIPolicyOutcomeSummary] = Field(default_factory=list)


class RAGRuntimeStatus(BaseModel):
    rag_enabled: bool = True
    hybrid_bge_enabled: bool = False
    bge_service_required: bool = False
    bge_service_url: str = ""
    query_generation_enabled: bool = True
    vector_top_k: int = 24
    rerank_top_k: int = 24
    final_top_k: int = 5
    status: str = "disabled"
    message: str = ""
    textbook_rag_enabled: bool = False
    textbook_rag_status: str = "disabled"
    textbook_rag_message: str = ""
    textbook_rag_index: str = ""
    textbook_rag_models: dict[str, str] = Field(default_factory=dict)
    textbook_rag_diagnostics: dict[str, Any] = Field(default_factory=dict)


class AIProviderRoleUpdate(BaseModel):
    provider: str = Field(default="openai", pattern="^openai$")
    base_url: str = ""
    model: str = ""
    api_key: str | None = None


class AIProviderRoleResponse(BaseModel):
    role: str
    provider: str = "openai"
    base_url: str = ""
    model: str = ""
    api_key_configured: bool = False
    api_key_fingerprint: str | None = None


class TextbookRAGConfigurationUpdate(BaseModel):
    enabled: bool = False
    elasticsearch_url: str = ""
    index_name: str = "canonical-rag-chunks-qwen-v1"
    embedding: AIProviderRoleUpdate = Field(default_factory=AIProviderRoleUpdate)
    rerank: AIProviderRoleUpdate = Field(default_factory=AIProviderRoleUpdate)
    embedding_dimension: int = Field(default=1024, ge=1)
    keyword_top_k: int = Field(default=16, ge=1, le=100)
    vector_top_k: int = Field(default=24, ge=1, le=100)
    rerank_top_k: int = Field(default=9, ge=1, le=100)
    final_top_k: int = Field(default=5, ge=1, le=30)
    min_rerank_score: float = 0.0
    timeout_seconds: float = Field(default=8.0, ge=0.5, le=60.0)


class TextbookRAGConfigurationResponse(BaseModel):
    enabled: bool = False
    elasticsearch_url: str = ""
    index_name: str = "canonical-rag-chunks-qwen-v1"
    embedding: AIProviderRoleResponse
    rerank: AIProviderRoleResponse
    embedding_dimension: int = 1024
    keyword_top_k: int = 16
    vector_top_k: int = 24
    rerank_top_k: int = 9
    final_top_k: int = 5
    min_rerank_score: float = 0.0
    timeout_seconds: float = 8.0


class AIConfigurationUpdate(BaseModel):
    provider: str = Field(default="openai", pattern="^openai$")
    base_url: str = ""
    model: str = ""
    api_key: str | None = None
    connection_check_interval_minutes: int = Field(default=30, ge=5, le=1440)
    enabled_features: AIEnabledFeatureScopes = Field(default_factory=AIEnabledFeatureScopes)
    chat_provider: AIProviderRoleUpdate | None = None
    textbook_rag: TextbookRAGConfigurationUpdate | None = None


class AIStatusSummary(BaseModel):
    ready: bool
    message: str
    effective_mode: str
    connectivity_status: str = Field(default="not_configured", pattern="^(not_configured|untested|connected|failed|stale)$")
    last_checked_at: datetime | None = None
    last_check_message: str | None = None
    check_interval_minutes: int = 30
    next_check_due_at: datetime | None = None
    recent_request_count: int = 0
    recent_error_count: int = 0
    last_request_at: datetime | None = None
    last_error_at: datetime | None = None
    usage_buckets: list[AIUsageBucket] = Field(default_factory=list)
    usage_trends: dict[str, AIUsageTrend] = Field(default_factory=dict)
    last_request_summary: AILastRequestSummary | None = None


class AIReasoningSummaryCapability(BaseModel):
    enabled: bool = False
    status: str = Field(
        default="untested",
        pattern="^(not_configured|untested|supported|unsupported|failed)$",
    )
    source: str = Field(default="agent_trace", pattern="^(reasoning_summary|agent_trace)$")
    message: str = ""
    last_checked_at: datetime | None = None


class AIConfigurationResponse(BaseModel):
    provider: str
    base_url: str
    model: str
    connection_check_interval_minutes: int = 30
    api_key_configured: bool
    api_key_fingerprint: str | None = None
    enabled_features: AIEnabledFeatureScopes = Field(default_factory=AIEnabledFeatureScopes)
    status: AIStatusSummary
    reasoning_summary: AIReasoningSummaryCapability = Field(default_factory=AIReasoningSummaryCapability)
    student_ai_policy: StudentAIPolicyStatus = Field(default_factory=StudentAIPolicyStatus)
    rag_runtime: RAGRuntimeStatus = Field(default_factory=RAGRuntimeStatus)
    chat_provider: AIProviderRoleResponse | None = None
    textbook_rag: TextbookRAGConfigurationResponse | None = None
    can_edit: bool = False


class PlatformSettingsResponse(BaseModel):
    settings: LearningBehaviorSettings
    can_edit: bool = False


_memory_settings: dict[str, dict[str, Any]] = {}

_CREATE_PLATFORM_SETTINGS_SQL = """
CREATE TABLE IF NOT EXISTS platform_settings (
  key text PRIMARY KEY,
  value jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
)
"""


def _model_dump(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _defaults_for_key(key: str) -> dict[str, Any]:
    if key == LEARNING_SETTINGS_KEY:
        return _model_dump(LearningBehaviorSettings())
    if key == AI_CONFIGURATION_KEY:
        settings = get_settings()
        return _model_dump(
            AIConfigurationUpdate(
                provider="openai",
                base_url=settings.agent_llm_base_url,
                model=settings.agent_llm_model,
                chat_provider=AIProviderRoleUpdate(
                    base_url=settings.agent_llm_base_url,
                    model=settings.agent_llm_model,
                ),
                textbook_rag=TextbookRAGConfigurationUpdate(
                    enabled=settings.textbook_rag_enabled,
                    elasticsearch_url=settings.textbook_rag_elasticsearch_url or settings.video_library_search_url,
                    index_name=settings.textbook_rag_elasticsearch_index,
                    embedding=AIProviderRoleUpdate(
                        base_url=settings.textbook_rag_embedding_base_url,
                        model=settings.textbook_rag_embedding_model,
                    ),
                    rerank=AIProviderRoleUpdate(
                        base_url=settings.textbook_rag_rerank_base_url,
                        model=settings.textbook_rag_rerank_model,
                    ),
                    embedding_dimension=settings.textbook_rag_embedding_dimension,
                    keyword_top_k=settings.rag_keyword_top_k,
                    vector_top_k=settings.rag_vector_top_k,
                    rerank_top_k=settings.rag_rerank_top_k,
                    final_top_k=settings.rag_final_top_k,
                    min_rerank_score=settings.textbook_rag_min_rerank_score,
                    timeout_seconds=settings.textbook_rag_timeout_seconds,
                ),
            )
        )
    return {}


def _json_param(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _postgres_enabled() -> bool:
    return get_settings().data_backend == "postgres"


def _ensure_table(session: Any) -> None:
    session.execute(text(_CREATE_PLATFORM_SETTINGS_SQL))


def _load_setting_value(key: str) -> dict[str, Any]:
    if not _postgres_enabled():
        return dict(_memory_settings.get(key) or _defaults_for_key(key))
    try:
        with db_session() as session:
            _ensure_table(session)
            row = session.execute(
                text("SELECT value FROM platform_settings WHERE key = :key"),
                {"key": key},
            ).mappings().first()
            if row:
                return dict(row["value"] or {})
            value = _defaults_for_key(key)
            session.execute(
                text(
                    """
                    INSERT INTO platform_settings (key, value)
                    VALUES (:key, CAST(:value AS jsonb))
                    ON CONFLICT (key) DO NOTHING
                    """
                ),
                {"key": key, "value": _json_param(value)},
            )
            return value
    except SQLAlchemyError:
        return _defaults_for_key(key)


def _save_setting_value(key: str, value: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    if not _postgres_enabled():
        _memory_settings[key] = dict(value)
        return value
    with db_session() as session:
        _ensure_table(session)
        session.execute(
            text(
                """
                INSERT INTO platform_settings (key, value, updated_by)
                VALUES (:key, CAST(:value AS jsonb), CAST(:updated_by AS uuid))
                ON CONFLICT (key) DO UPDATE SET
                  value = EXCLUDED.value,
                  updated_by = EXCLUDED.updated_by,
                  updated_at = now()
                """
            ),
            {"key": key, "value": _json_param(value), "updated_by": user_id},
        )
    return value


def get_learning_behavior_settings() -> LearningBehaviorSettings:
    return LearningBehaviorSettings(**_load_setting_value(LEARNING_SETTINGS_KEY))


def save_learning_behavior_settings(
    settings: LearningBehaviorSettings,
    user_id: str | None = None,
) -> LearningBehaviorSettings:
    value = _save_setting_value(LEARNING_SETTINGS_KEY, _model_dump(settings), user_id)
    return LearningBehaviorSettings(**value)


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _as_int(value: Any, default: int, *, minimum: int = 1, maximum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    parsed = max(minimum, parsed)
    if maximum is not None:
        parsed = min(maximum, parsed)
    return parsed


def _as_float(value: Any, default: float, *, minimum: float | None = None, maximum: float | None = None) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    if minimum is not None:
        parsed = max(minimum, parsed)
    if maximum is not None:
        parsed = min(maximum, parsed)
    return parsed


def _role_payload(stored: Any, *, base_url: str = "", model: str = "", api_key: str = "") -> dict[str, Any]:
    payload = stored if isinstance(stored, dict) else {}
    return {
        "provider": "openai",
        "base_url": str(payload.get("base_url") or base_url or "").strip().rstrip("/"),
        "model": str(payload.get("model") or model or "").strip(),
        "api_key": str(payload.get("api_key") or api_key or "").strip(),
    }


def _textbook_rag_payload(stored: Any, base: Settings) -> dict[str, Any]:
    payload = stored if isinstance(stored, dict) else {}
    embedding = _role_payload(
        payload.get("embedding"),
        base_url=base.textbook_rag_embedding_base_url,
        model=base.textbook_rag_embedding_model,
        api_key=base.textbook_rag_embedding_api_key,
    )
    rerank = _role_payload(
        payload.get("rerank"),
        base_url=base.textbook_rag_rerank_base_url,
        model=base.textbook_rag_rerank_model,
        api_key=base.textbook_rag_rerank_api_key,
    )
    return {
        "enabled": _as_bool(payload.get("enabled"), base.textbook_rag_enabled),
        "elasticsearch_url": str(
            payload.get("elasticsearch_url")
            or base.textbook_rag_elasticsearch_url
            or base.video_library_search_url
            or ""
        ).strip().rstrip("/"),
        "index_name": str(payload.get("index_name") or base.textbook_rag_elasticsearch_index).strip(),
        "embedding": embedding,
        "rerank": rerank,
        "embedding_dimension": _as_int(
            payload.get("embedding_dimension"),
            base.textbook_rag_embedding_dimension,
            minimum=1,
        ),
        "keyword_top_k": _as_int(payload.get("keyword_top_k"), base.rag_keyword_top_k, minimum=1, maximum=100),
        "vector_top_k": _as_int(payload.get("vector_top_k"), base.rag_vector_top_k, minimum=1, maximum=100),
        "rerank_top_k": _as_int(payload.get("rerank_top_k"), base.rag_rerank_top_k, minimum=1, maximum=100),
        "final_top_k": _as_int(payload.get("final_top_k"), base.rag_final_top_k, minimum=1, maximum=30),
        "min_rerank_score": _as_float(
            payload.get("min_rerank_score"),
            base.textbook_rag_min_rerank_score,
        ),
        "timeout_seconds": _as_float(
            payload.get("timeout_seconds"),
            base.textbook_rag_timeout_seconds,
            minimum=0.5,
            maximum=60.0,
        ),
    }


def _effective_ai_configuration_payload() -> dict[str, Any]:
    base = get_settings()
    stored = _load_setting_value(AI_CONFIGURATION_KEY)
    chat = _role_payload(
        stored.get("chat_provider"),
        base_url=str(stored.get("base_url") or base.agent_llm_base_url),
        model=str(stored.get("model") or base.agent_llm_model),
        api_key=str(stored.get("api_key") or base.agent_llm_api_key or ""),
    )
    interval_minutes = _normalized_check_interval(stored.get("connection_check_interval_minutes"))
    features = stored.get("enabled_features") or {}
    textbook_rag = _textbook_rag_payload(stored.get("textbook_rag"), base)
    return {
        "provider": "openai",
        "base_url": chat["base_url"],
        "model": chat["model"],
        "api_key": chat["api_key"],
        "chat_provider": chat,
        "textbook_rag": textbook_rag,
        "connection_check_interval_minutes": interval_minutes,
        "enabled_features": _model_dump(AIEnabledFeatureScopes(**features)),
        "connection_check": stored.get("connection_check") if isinstance(stored.get("connection_check"), dict) else {},
    }


def _api_key_fingerprint(api_key: str) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "********"
    return f"{api_key[:3]}...{api_key[-4:]}"


def _role_response(role: str, payload: dict[str, Any]) -> AIProviderRoleResponse:
    api_key = str(payload.get("api_key") or "")
    return AIProviderRoleResponse(
        role=role,
        provider="openai",
        base_url=str(payload.get("base_url") or ""),
        model=str(payload.get("model") or ""),
        api_key_configured=bool(api_key),
        api_key_fingerprint=_api_key_fingerprint(api_key),
    )


def _textbook_rag_response(payload: dict[str, Any]) -> TextbookRAGConfigurationResponse:
    return TextbookRAGConfigurationResponse(
        enabled=bool(payload.get("enabled")),
        elasticsearch_url=str(payload.get("elasticsearch_url") or ""),
        index_name=str(payload.get("index_name") or ""),
        embedding=_role_response("textbook_embedding", payload.get("embedding") or {}),
        rerank=_role_response("textbook_rerank", payload.get("rerank") or {}),
        embedding_dimension=int(payload.get("embedding_dimension") or 1024),
        keyword_top_k=int(payload.get("keyword_top_k") or 16),
        vector_top_k=int(payload.get("vector_top_k") or 24),
        rerank_top_k=int(payload.get("rerank_top_k") or 9),
        final_top_k=int(payload.get("final_top_k") or 5),
        min_rerank_score=float(payload.get("min_rerank_score") or 0.0),
        timeout_seconds=float(payload.get("timeout_seconds") or 8.0),
    )


def _agent_usage_trend(session: Any, range_key: str) -> dict[str, Any]:
    if range_key == "1d":
        start_expression = "date_trunc('hour', now()) - interval '23 hours'"
        end_expression = "date_trunc('hour', now())"
        step = "1 hour"
        bucket_format = "YYYY-MM-DD HH24:00"
        bucket_unit = "hour"
    elif range_key == "30d":
        start_expression = "date_trunc('day', now()) - interval '29 days'"
        end_expression = "date_trunc('day', now())"
        step = "1 day"
        bucket_format = "YYYY-MM-DD"
        bucket_unit = "day"
    else:
        half_day_anchor = (
            "date_trunc('day', now()) + "
            "CASE WHEN EXTRACT(hour FROM now()) >= 12 "
            "THEN interval '12 hours' ELSE interval '0 hours' END"
        )
        start_expression = f"{half_day_anchor} - interval '156 hours'"
        end_expression = half_day_anchor
        step = "12 hours"
        bucket_format = "YYYY-MM-DD HH24:00"
        bucket_unit = "half_day"
    rows = session.execute(
        text(
            f"""
            WITH buckets AS (
              SELECT generate_series(
                {start_expression},
                {end_expression},
                interval '{step}'
              ) AS bucket_start
            )
            SELECT
              to_char(buckets.bucket_start, '{bucket_format}') AS bucket,
              COUNT(agent_logs.id)::int AS request_count,
              COUNT(agent_logs.id) FILTER (
                WHERE response_metadata ? 'error'
                   OR response_metadata->>'status' = 'error'
              )::int AS error_count
            FROM buckets
            LEFT JOIN agent_logs
              ON agent_logs.created_at >= buckets.bucket_start
             AND agent_logs.created_at < buckets.bucket_start + interval '{step}'
            GROUP BY buckets.bucket_start
            ORDER BY buckets.bucket_start
            """
        )
    ).mappings().all()
    return {
        "range": range_key,
        "bucket_unit": bucket_unit,
        "buckets": [dict(row) for row in rows],
    }


def _channel_label(user_role: Any) -> str:
    if str(user_role or "").lower() == "student":
        return "学生 AI 学习助手"
    return "后台 Agent"

POLICY_MODE_LABELS = {
    "normal_answer": "普通课程回答",
    "refuse_out_of_scope": "课程外拒答",
    "safe_experiment_guidance": "实验安全引导",
    "assessment_hint": "测验提示",
    "needs_platform_evidence": "平台证据检索",
}
STUDENT_AI_POLICY_COVERAGE = [
    "课程外请求",
    "危险实验请求",
    "索要测验答案",
    "实验现象/视频/资料证据",
    "普通课程问答",
]


def _policy_outcome_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        mode = str(row.get("mode") or "unknown")
        counts[mode] = counts.get(mode, 0) + int(row.get("count") or 0)
    return [
        {"mode": mode, "label": POLICY_MODE_LABELS.get(mode, "其他判定"), "count": count}
        for mode, count in counts.items()
        if count > 0
    ]


def _student_ai_policy_status(effective: dict[str, Any], log_summary: dict[str, Any]) -> StudentAIPolicyStatus:
    outcomes = [
        StudentAIPolicyOutcomeSummary(**item)
        for item in _policy_outcome_summaries(log_summary.get("policy_outcomes") or [])
    ]
    return StudentAIPolicyStatus(
        active=bool(effective.get("model") and effective.get("api_key")),
        model=str(effective.get("model") or ""),
        coverage=list(STUDENT_AI_POLICY_COVERAGE),
        recent_decision_count=int(log_summary.get("policy_recent_decision_count") or 0),
        invalid_decision_count=int(log_summary.get("policy_invalid_decision_count") or 0),
        outcomes=outcomes,
    )


def _textbook_rag_runtime_status(textbook_rag: dict[str, Any], *, rag_enabled: bool) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "enabled": bool(textbook_rag.get("enabled")),
        "elasticsearch_url_configured": bool(textbook_rag.get("elasticsearch_url")),
        "embedding_configured": bool((textbook_rag.get("embedding") or {}).get("model"))
        and bool((textbook_rag.get("embedding") or {}).get("api_key")),
        "rerank_configured": bool((textbook_rag.get("rerank") or {}).get("model"))
        and bool((textbook_rag.get("rerank") or {}).get("api_key")),
    }
    models = {
        "embedding": str((textbook_rag.get("embedding") or {}).get("model") or ""),
        "rerank": str((textbook_rag.get("rerank") or {}).get("model") or ""),
    }
    if not rag_enabled:
        return {
            "enabled": False,
            "status": "disabled",
            "message": "RAG 已关闭，教材 RAG 不会用于教师出题。",
            "models": models,
            "diagnostics": diagnostics,
        }
    if not textbook_rag.get("enabled"):
        return {
            "enabled": False,
            "status": "disabled",
            "message": "教材 RAG 未启用。",
            "models": models,
            "diagnostics": diagnostics,
        }
    if not textbook_rag.get("elasticsearch_url"):
        return {
            "enabled": True,
            "status": "elasticsearch_not_configured",
            "message": "教材 RAG 缺少 Elasticsearch 地址。",
            "models": models,
            "diagnostics": diagnostics,
        }
    if not diagnostics["embedding_configured"]:
        return {
            "enabled": True,
            "status": "embedding_not_configured",
            "message": "教材 RAG 缺少 Embedding 模型或密钥。",
            "models": models,
            "diagnostics": diagnostics,
        }
    if not diagnostics["rerank_configured"]:
        return {
            "enabled": True,
            "status": "rerank_not_configured",
            "message": "教材 RAG 缺少 Rerank 模型或密钥。",
            "models": models,
            "diagnostics": diagnostics,
        }
    try:
        request = urllib.request.Request(
            f"{str(textbook_rag['elasticsearch_url']).rstrip('/')}/{textbook_rag['index_name']}",
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=float(textbook_rag.get("timeout_seconds") or 8.0)) as response:
            index_payload = json.loads(response.read().decode("utf-8"))
        index_info = index_payload.get(textbook_rag["index_name"], {}) if isinstance(index_payload, dict) else {}
        mappings = index_info.get("mappings") if isinstance(index_info, dict) else {}
        meta = mappings.get("_meta") if isinstance(mappings, dict) else {}
        diagnostics["index_exists"] = True
        diagnostics["index_metadata"] = meta if isinstance(meta, dict) else {}
    except urllib.error.HTTPError as exc:
        diagnostics["index_exists"] = False
        diagnostics["elasticsearch_error"] = f"HTTP {exc.code}"
        return {
            "enabled": True,
            "status": "index_missing" if exc.code == 404 else "elasticsearch_error",
            "message": "教材 RAG 索引不存在。" if exc.code == 404 else "教材 RAG Elasticsearch 检查失败。",
            "models": models,
            "diagnostics": diagnostics,
        }
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        diagnostics["elasticsearch_error"] = f"{exc.__class__.__name__}: {str(exc)[:160]}"
        return {
            "enabled": True,
            "status": "elasticsearch_unreachable",
            "message": "教材 RAG Elasticsearch 不可达。",
            "models": models,
            "diagnostics": diagnostics,
        }
    meta = diagnostics.get("index_metadata") if isinstance(diagnostics.get("index_metadata"), dict) else {}
    expected_model = str((textbook_rag.get("embedding") or {}).get("model") or "")
    expected_dim = int(textbook_rag.get("embedding_dimension") or 0)
    indexed_model = str(meta.get("embedding_model") or "")
    indexed_dim = int(meta.get("embedding_dimension") or 0) if str(meta.get("embedding_dimension") or "").isdigit() else 0
    if meta and (indexed_model != expected_model or (indexed_dim and indexed_dim != expected_dim)):
        return {
            "enabled": True,
            "status": "index_stale",
            "message": "教材 RAG 索引模型信息与当前 Embedding 配置不一致。",
            "models": models,
            "diagnostics": diagnostics,
        }
    return {
        "enabled": True,
        "status": "healthy",
        "message": "教材 RAG 已配置，Elasticsearch 索引可访问。",
        "models": models,
        "diagnostics": diagnostics,
    }


def _rag_runtime_status(features: dict[str, Any], textbook_rag: dict[str, Any] | None = None) -> RAGRuntimeStatus:
    settings = get_settings()
    rag_enabled = bool(features.get("rag_access_enabled", True))
    hybrid_enabled = bool(settings.rag_hybrid_bge_enabled)
    bge_required = bool(rag_enabled and hybrid_enabled)
    textbook_status = _textbook_rag_runtime_status(textbook_rag or {}, rag_enabled=rag_enabled)
    if not rag_enabled:
        status = "disabled"
        message = "RAG 已关闭，BGE CPU 服务无需启动。"
    elif hybrid_enabled:
        status = "bge_configured"
        message = "Hybrid BGE RAG 已启用，后端会通过独立 BGE 服务进行向量召回与重排。"
    else:
        status = "legacy"
        message = "当前使用现有来源/关键词 RAG，未启用 BGE sidecar。"
    return RAGRuntimeStatus(
        rag_enabled=rag_enabled,
        hybrid_bge_enabled=hybrid_enabled,
        bge_service_required=bge_required,
        bge_service_url=settings.rag_bge_service_url,
        query_generation_enabled=bool(settings.rag_query_generation_enabled),
        vector_top_k=int(settings.rag_vector_top_k),
        rerank_top_k=int(settings.rag_rerank_top_k),
        final_top_k=int(settings.rag_final_top_k),
        status=status,
        message=message,
        textbook_rag_enabled=bool(textbook_status["enabled"]),
        textbook_rag_status=str(textbook_status["status"]),
        textbook_rag_message=str(textbook_status["message"]),
        textbook_rag_index=str((textbook_rag or {}).get("index_name") or ""),
        textbook_rag_models=textbook_status["models"],
        textbook_rag_diagnostics=textbook_status["diagnostics"],
    )


def _agent_log_summary() -> dict[str, Any]:
    if not _postgres_enabled():
        return {"usage_buckets": [], "usage_trends": {}}
    try:
        with db_session() as session:
            row = session.execute(
                text(
                    """
                    SELECT
                      COUNT(*)::int AS recent_request_count,
                      MAX(created_at) AS last_request_at,
                      COUNT(*) FILTER (
                        WHERE response_metadata ? 'error'
                           OR response_metadata->>'status' = 'error'
                      )::int AS recent_error_count,
                      MAX(created_at) FILTER (
                        WHERE response_metadata ? 'error'
                           OR response_metadata->>'status' = 'error'
                      ) AS last_error_at
                    FROM agent_logs
                    WHERE created_at >= now() - interval '24 hours'
                    """
                )
            ).mappings().first()
            latest = session.execute(
                text(
                    """
                    SELECT
                      created_at AS called_at,
                      user_role,
                      CASE
                        WHEN response_metadata ? 'error'
                           OR response_metadata->>'status' = 'error'
                        THEN 'error'
                        ELSE 'success'
                      END AS status
                    FROM agent_logs
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                )
            ).mappings().first()
            policy_rows = session.execute(
                text(
                    """
                    SELECT
                      COALESCE(response_metadata->'policy_decision'->>'mode', 'unknown') AS mode,
                      COUNT(*)::int AS count
                    FROM agent_logs
                    WHERE created_at >= now() - interval '24 hours'
                      AND LOWER(COALESCE(user_role, '')) = 'student'
                      AND response_metadata ? 'policy_decision'
                    GROUP BY mode
                    ORDER BY count DESC
                    """
                )
            ).mappings().all()
            policy_invalid = session.execute(
                text(
                    """
                    SELECT COUNT(*)::int AS count
                    FROM agent_logs
                    WHERE created_at >= now() - interval '24 hours'
                      AND LOWER(COALESCE(user_role, '')) = 'student'
                      AND response_metadata ? 'policy_decision'
                      AND response_metadata->'policy_decision'->>'valid' = 'false'
                    """
                )
            ).mappings().first()
            usage_trends = {
                "1d": _agent_usage_trend(session, "1d"),
                "7d": _agent_usage_trend(session, "7d"),
                "30d": _agent_usage_trend(session, "30d"),
            }
            summary = dict(row or {})
            summary["usage_buckets"] = usage_trends["7d"]["buckets"]
            summary["usage_trends"] = usage_trends
            summary["policy_outcomes"] = [dict(policy_row) for policy_row in policy_rows]
            summary["policy_recent_decision_count"] = sum(int(policy_row.get("count") or 0) for policy_row in policy_rows)
            summary["policy_invalid_decision_count"] = int((policy_invalid or {}).get("count") or 0)
            if latest:
                latest_data = dict(latest)
                summary["last_request_summary"] = {
                    "called_at": latest_data["called_at"],
                    "channel": _channel_label(latest_data.get("user_role")),
                    "status": latest_data["status"],
                }
            return summary
    except SQLAlchemyError:
        return {"usage_buckets": [], "usage_trends": {}}


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalized_check_interval(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 30
    return max(5, min(parsed, 1440))


def _connection_check_due(effective: dict[str, Any]) -> bool:
    if not effective["model"] or not effective["api_key"]:
        return False
    check = effective.get("connection_check") or {}
    checked_at = _parse_datetime(check.get("checked_at"))
    if not checked_at:
        return True
    interval_minutes = _normalized_check_interval(effective.get("connection_check_interval_minutes"))
    return checked_at + timedelta(minutes=interval_minutes) <= datetime.now(timezone.utc)


def _connection_status(effective: dict[str, Any]) -> dict[str, Any]:
    interval_minutes = _normalized_check_interval(effective.get("connection_check_interval_minutes"))
    check = effective.get("connection_check") or {}
    checked_at = _parse_datetime(check.get("checked_at"))
    if not effective["model"] or not effective["api_key"]:
        return {
            "ready": False,
            "connectivity_status": "not_configured",
            "message": "请填写模型名称和 API Key，系统会按间隔自动检测连接",
            "effective_mode": "not_configured",
            "last_checked_at": checked_at,
            "last_check_message": check.get("message"),
            "check_interval_minutes": interval_minutes,
            "next_check_due_at": None,
        }
    raw_status = str(check.get("status") or "").strip()
    next_due_at = checked_at + timedelta(minutes=interval_minutes) if checked_at else None
    now = datetime.now(timezone.utc)
    if not raw_status:
        return {
            "ready": False,
            "connectivity_status": "untested",
            "message": "已填写配置，系统将按间隔自动检测 OpenAI API 连接",
            "effective_mode": "connection_untested",
            "last_checked_at": None,
            "last_check_message": None,
            "check_interval_minutes": interval_minutes,
            "next_check_due_at": None,
        }
    if raw_status == "connected" and next_due_at and next_due_at < now:
        return {
            "ready": False,
            "connectivity_status": "stale",
            "message": "上次连接检测已超过 30 分钟，建议重新检测",
            "effective_mode": "connection_stale",
            "last_checked_at": checked_at,
            "last_check_message": check.get("message"),
            "check_interval_minutes": interval_minutes,
            "next_check_due_at": next_due_at,
        }
    if raw_status == "connected":
        return {
            "ready": True,
            "connectivity_status": "connected",
            "message": "OpenAI API 连接正常",
            "effective_mode": "openai_api",
            "last_checked_at": checked_at,
            "last_check_message": check.get("message"),
            "check_interval_minutes": interval_minutes,
            "next_check_due_at": next_due_at,
        }
    return {
        "ready": False,
        "connectivity_status": "failed",
        "message": "OpenAI API 连接检测失败",
        "effective_mode": "connection_failed",
        "last_checked_at": checked_at,
        "last_check_message": check.get("message") or "请检查 API Key、Base URL 和模型名称。",
        "check_interval_minutes": interval_minutes,
        "next_check_due_at": next_due_at,
    }


def _reasoning_summary_capability_status(effective: dict[str, Any]) -> dict[str, Any]:
    check = effective.get("connection_check") or {}
    capabilities = check.get("capabilities") if isinstance(check.get("capabilities"), dict) else {}
    capability = capabilities.get("reasoning_summary") if isinstance(capabilities.get("reasoning_summary"), dict) else {}
    checked_at = _parse_datetime(capability.get("checked_at") or check.get("checked_at"))
    if not effective["model"] or not effective["api_key"]:
        return {
            "enabled": False,
            "status": "not_configured",
            "source": "agent_trace",
            "message": "Model and API key must be saved before reasoning summary can be tested.",
            "last_checked_at": checked_at,
        }
    status_value = str(capability.get("status") or "").strip()
    if not status_value:
        return {
            "enabled": False,
            "status": "untested",
            "source": "agent_trace",
            "message": "Reasoning summary capability has not been tested yet.",
            "last_checked_at": checked_at,
        }
    enabled = bool(capability.get("supported")) and status_value == "supported"
    return {
        "enabled": enabled,
        "status": status_value if status_value in {"supported", "unsupported", "failed"} else "untested",
        "source": "reasoning_summary" if enabled else "agent_trace",
        "message": str(capability.get("message") or ""),
        "last_checked_at": checked_at,
    }


def get_ai_configuration_response(can_edit: bool = False, auto_check: bool = True) -> AIConfigurationResponse:
    effective = _effective_ai_configuration_payload()
    if auto_check and _connection_check_due(effective):
        _run_ai_connection_check()
        effective = _effective_ai_configuration_payload()
    api_key = effective["api_key"]
    connection = _connection_status(effective)
    log_summary = _agent_log_summary()
    return AIConfigurationResponse(
        provider="openai",
        base_url=effective["base_url"],
        model=effective["model"],
        connection_check_interval_minutes=_normalized_check_interval(effective["connection_check_interval_minutes"]),
        api_key_configured=bool(api_key),
        api_key_fingerprint=_api_key_fingerprint(api_key),
        enabled_features=AIEnabledFeatureScopes(**effective["enabled_features"]),
        status=AIStatusSummary(
            ready=connection["ready"],
            message=connection["message"],
            effective_mode=connection["effective_mode"],
            connectivity_status=connection["connectivity_status"],
            last_checked_at=connection["last_checked_at"],
            last_check_message=connection["last_check_message"],
            check_interval_minutes=connection["check_interval_minutes"],
            next_check_due_at=connection["next_check_due_at"],
            recent_request_count=int(log_summary.get("recent_request_count") or 0),
            recent_error_count=int(log_summary.get("recent_error_count") or 0),
            last_request_at=log_summary.get("last_request_at"),
            last_error_at=log_summary.get("last_error_at"),
            usage_buckets=[
                AIUsageBucket(**bucket)
                for bucket in (log_summary.get("usage_buckets") or [])
                if isinstance(bucket, dict)
            ],
            usage_trends={
                str(key): AIUsageTrend(**value)
                for key, value in (log_summary.get("usage_trends") or {}).items()
                if isinstance(value, dict)
            },
            last_request_summary=AILastRequestSummary(**log_summary["last_request_summary"])
            if isinstance(log_summary.get("last_request_summary"), dict)
            else None,
        ),
        reasoning_summary=AIReasoningSummaryCapability(**_reasoning_summary_capability_status(effective)),
        student_ai_policy=_student_ai_policy_status(effective, log_summary),
        rag_runtime=_rag_runtime_status(effective["enabled_features"], effective.get("textbook_rag")),
        chat_provider=_role_response("chat_completion", effective["chat_provider"]),
        textbook_rag=_textbook_rag_response(effective["textbook_rag"]),
        can_edit=can_edit,
    )


def save_ai_configuration(payload: AIConfigurationUpdate, user_id: str | None = None) -> AIConfigurationResponse:
    existing = _load_setting_value(AI_CONFIGURATION_KEY)
    incoming = _model_dump(payload)
    value = dict(existing)
    value.update(
        {
            "provider": "openai",
            "base_url": incoming.get("base_url") or "",
            "model": incoming.get("model") or "",
            "connection_check_interval_minutes": incoming.get("connection_check_interval_minutes"),
            "enabled_features": incoming.get("enabled_features") or _model_dump(AIEnabledFeatureScopes()),
        }
    )
    value["provider"] = "openai"
    new_secret = (payload.api_key or "").strip()
    if new_secret:
        value["api_key"] = new_secret
    elif existing.get("api_key"):
        value["api_key"] = existing["api_key"]
    else:
        value.pop("api_key", None)
    chat_incoming = incoming.get("chat_provider") if isinstance(incoming.get("chat_provider"), dict) else None
    if chat_incoming is not None:
        existing_chat = existing.get("chat_provider") if isinstance(existing.get("chat_provider"), dict) else {}
        chat_value = {
            "provider": "openai",
            "base_url": str(chat_incoming.get("base_url") or value.get("base_url") or "").strip().rstrip("/"),
            "model": str(chat_incoming.get("model") or value.get("model") or "").strip(),
        }
        chat_secret = str(chat_incoming.get("api_key") or "").strip()
        if chat_secret:
            chat_value["api_key"] = chat_secret
        elif existing_chat.get("api_key"):
            chat_value["api_key"] = existing_chat["api_key"]
        elif value.get("api_key"):
            chat_value["api_key"] = value["api_key"]
        value["chat_provider"] = chat_value
        value["base_url"] = chat_value["base_url"]
        value["model"] = chat_value["model"]
        if chat_value.get("api_key"):
            value["api_key"] = chat_value["api_key"]
    else:
        existing_chat = existing.get("chat_provider") if isinstance(existing.get("chat_provider"), dict) else {}
        chat_value = {
            "provider": "openai",
            "base_url": str(value.get("base_url") or "").strip().rstrip("/"),
            "model": str(value.get("model") or "").strip(),
        }
        if new_secret:
            chat_value["api_key"] = new_secret
        elif existing_chat.get("api_key"):
            chat_value["api_key"] = existing_chat["api_key"]
        elif existing.get("api_key"):
            chat_value["api_key"] = existing["api_key"]
        value["chat_provider"] = chat_value
    textbook_incoming = incoming.get("textbook_rag") if isinstance(incoming.get("textbook_rag"), dict) else None
    if textbook_incoming is not None:
        existing_textbook = existing.get("textbook_rag") if isinstance(existing.get("textbook_rag"), dict) else {}
        textbook_value = {**existing_textbook, **textbook_incoming}
        for role_name in ("embedding", "rerank"):
            role_incoming = (
                textbook_incoming.get(role_name)
                if isinstance(textbook_incoming.get(role_name), dict)
                else {}
            )
            existing_role = (
                existing_textbook.get(role_name)
                if isinstance(existing_textbook.get(role_name), dict)
                else {}
            )
            role_value = {
                "provider": "openai",
                "base_url": str(role_incoming.get("base_url") or existing_role.get("base_url") or "").strip().rstrip("/"),
                "model": str(role_incoming.get("model") or existing_role.get("model") or "").strip(),
            }
            role_secret = str(role_incoming.get("api_key") or "").strip()
            if role_secret:
                role_value["api_key"] = role_secret
            elif existing_role.get("api_key"):
                role_value["api_key"] = existing_role["api_key"]
            textbook_value[role_name] = role_value
        value["textbook_rag"] = textbook_value
    previous_effective = _effective_ai_configuration_payload()
    if (
        previous_effective.get("model") == value.get("model")
        and previous_effective.get("base_url") == value.get("base_url")
        and previous_effective.get("api_key") == value.get("api_key", "")
        and existing.get("connection_check")
    ):
        value["connection_check"] = existing["connection_check"]
    _save_setting_value(AI_CONFIGURATION_KEY, value, user_id)
    _run_ai_connection_check(user_id)
    return get_ai_configuration_response(can_edit=True, auto_check=False)


def _check_openai_chat_connection(client: Any, effective: dict[str, Any]) -> None:
    response = client.chat.completions.create(
        model=effective["model"],
        temperature=0,
        max_tokens=1,
        messages=[
            {"role": "system", "content": "You are a connectivity probe. Reply with one short token."},
            {"role": "user", "content": "ping"},
        ],
    )
    if not getattr(response, "choices", None):
        raise RuntimeError("OpenAI-compatible chat completion returned no choices")


def _probe_reasoning_summary_capability(client: Any, effective: dict[str, Any], checked_at: str) -> dict[str, Any]:
    responses = getattr(client, "responses", None)
    if responses is None or not hasattr(responses, "stream"):
        return {
            "supported": False,
            "status": "unsupported",
            "checked_at": checked_at,
            "message": "Responses streaming API is not available; student AI will show agent execution trace.",
        }
    event_types: set[str] = set()
    try:
        with responses.stream(
            model=effective["model"],
            instructions="You are a capability probe. Answer with OK only.",
            input="Return OK.",
            reasoning={"summary": "auto", "effort": "minimal"},
            temperature=0,
            max_output_tokens=16,
        ) as stream:
            for event in stream:
                event_type = str(getattr(event, "type", "") or "")
                if event_type:
                    event_types.add(event_type)
                if event_type in {"response.reasoning_summary_text.delta", "response.reasoning_summary_text.done"}:
                    return {
                        "supported": True,
                        "status": "supported",
                        "checked_at": checked_at,
                        "message": "Reasoning summary events were detected; student AI will show model reasoning summaries.",
                    }
        return {
            "supported": False,
            "status": "unsupported",
            "checked_at": checked_at,
            "message": (
                "Responses API completed but did not emit reasoning summary events; "
                "student AI will show agent execution trace."
            ),
            "observed_event_types": sorted(event_types)[:12],
        }
    except Exception as exc:
        return {
            "supported": False,
            "status": "unsupported",
            "checked_at": checked_at,
            "message": f"Reasoning summary probe failed: {str(exc)[:180]}",
        }


def _run_ai_connection_check(user_id: str | None = None) -> None:
    existing = _load_setting_value(AI_CONFIGURATION_KEY)
    effective = _effective_ai_configuration_payload()
    checked_at = datetime.now(timezone.utc).isoformat()
    if not effective["model"] or not effective["api_key"]:
        existing["connection_check"] = {
            "status": "not_configured",
            "checked_at": checked_at,
            "message": "请先保存模型名称和 API Key。",
            "capabilities": {
                "reasoning_summary": {
                    "supported": False,
                    "status": "not_configured",
                    "checked_at": checked_at,
                    "message": "Model and API key are required before reasoning summary can be tested.",
                }
            },
        }
        _save_setting_value(AI_CONFIGURATION_KEY, existing, user_id)
        return
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=effective["api_key"],
            base_url=effective["base_url"] or None,
            timeout=8.0,
        )
        _check_openai_chat_connection(client, effective)
        reasoning_summary = _probe_reasoning_summary_capability(client, effective, checked_at)
        existing["connection_check"] = {
            "status": "connected",
            "checked_at": checked_at,
            "message": f"模型 {effective['model']} 可访问。",
            "capabilities": {
                "reasoning_summary": reasoning_summary,
            },
        }
    except Exception as exc:
        existing["connection_check"] = {
            "status": "failed",
            "checked_at": checked_at,
            "message": str(exc)[:220] or "连接检测失败。",
            "capabilities": {
                "reasoning_summary": {
                    "supported": False,
                    "status": "failed",
                    "checked_at": checked_at,
                    "message": "OpenAI-compatible chat connection failed; reasoning summary was not tested.",
                }
            },
        }
    _save_setting_value(AI_CONFIGURATION_KEY, existing, user_id)


def check_ai_connection(user_id: str | None = None) -> AIConfigurationResponse:
    _run_ai_connection_check(user_id)
    return get_ai_configuration_response(can_edit=True, auto_check=False)


def effective_ai_settings(base_settings: Settings | None = None) -> Settings:
    base = base_settings or get_settings()
    effective = _effective_ai_configuration_payload()
    reasoning_summary = _reasoning_summary_capability_status(effective)
    reasoning_summary_enabled = bool(reasoning_summary["enabled"])
    return replace(
        base,
        agent_llm_provider=effective["provider"],
        agent_llm_base_url=effective["base_url"],
        agent_llm_api_key=effective["api_key"],
        agent_llm_model=effective["model"],
        agent_reasoning_summary_enabled=reasoning_summary_enabled,
        agent_reasoning_summary_mode="compatible" if reasoning_summary_enabled and effective["base_url"] else "auto",
    )


def effective_textbook_rag_settings() -> dict[str, Any]:
    return dict(_effective_ai_configuration_payload().get("textbook_rag") or {})


def ai_feature_enabled(feature_name: str) -> bool:
    features = get_ai_configuration_response().enabled_features
    return bool(getattr(features, feature_name, False))
