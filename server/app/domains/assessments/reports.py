from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from server.app.domains.assistant.agent import run_agent
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.domains.platform.settings import (
    _load_setting_value,
    _save_setting_value,
    effective_ai_settings,
    get_ai_configuration_response,
    get_learning_behavior_settings,
)
from server.app.domains.roster.classes import require_class_access
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings
from server.app.schemas import AgentAskRequest
from server.app.student_assessment_report_schemas import (
    AssessmentReportGeneratedText,
    AssessmentReportPromptSettings,
    AssessmentReportPromptSettingsResponse,
    AssessmentReportPromptSettingsUpdate,
    StudentAssessmentReport,
    StudentAssessmentReportListResponse,
    StudentAssessmentReportSummary,
)
from server.app.student_smart_assessment_schemas import StudentSmartAssessmentReport


REPORT_PROMPT_SETTINGS_KEY = "assessment_report_prompts"
REPORT_TYPES = {"pretest", "smart", "custom", "point", "posttest"}
SUPPORTED_PROMPT_VARIABLES = [
    "student_name",
    "student_id",
    "assessment_type",
    "score",
    "correct_count",
    "total_count",
    "correct_rate",
    "wrong_count",
    "wrong_questions",
    "mastery_changes",
    "experiment_points",
]

DEFAULT_SUMMARY_PROMPT = (
    "请基于本次测评报告生成一段中性的学习记录总结，面向学生和老师共同阅读。"
    "需要概括测评类型、得分、掌握变化、主要薄弱实验或点位，并给出下一步复习建议。"
    "不要使用“你”式聊天口吻，不要出现 AI、模型、提示词等字样。控制在 220 字以内。\n\n"
    "学生：{{student_name}}（{{student_id}}）\n"
    "测评：{{assessment_type}}\n"
    "成绩：{{score}} 分，{{correct_count}}/{{total_count}} 题，正确率 {{correct_rate}}\n"
    "错题数：{{wrong_count}}\n"
    "涉及实验或点位：{{experiment_points}}\n"
    "掌握度变化：{{mastery_changes}}\n"
)

DEFAULT_MISTAKE_PROMPT = (
    "请基于本次测评的错题生成一段中性的错题讲解，面向学生和老师共同阅读。"
    "先概括共同错因，再按错题说明正确思路和复习抓手。"
    "只解释本次已提交错题，不要泄露未提交题目的答案，不要出现 AI、模型、提示词等字样。"
    "如果没有错题，简短说明本次没有错题。\n\n"
    "测评：{{assessment_type}}\n"
    "错题：{{wrong_questions}}\n"
)

_CREATE_REPORT_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS student_assessment_reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id text NOT NULL,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  report_type text NOT NULL CHECK (report_type IN ('pretest', 'smart', 'custom', 'point', 'posttest')),
  source_session_id uuid NOT NULL,
  source_table text NOT NULL,
  title text NOT NULL,
  score numeric NOT NULL DEFAULT 0,
  correct_count int NOT NULL DEFAULT 0,
  total_count int NOT NULL DEFAULT 0,
  correct_rate numeric NOT NULL DEFAULT 0,
  wrong_count int NOT NULL DEFAULT 0,
  summary jsonb NOT NULL DEFAULT '{}'::jsonb,
  mistake_explanation jsonb NOT NULL DEFAULT '{}'::jsonb,
  prompt_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  completed_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (report_type, source_session_id)
);

CREATE INDEX IF NOT EXISTS idx_student_assessment_reports_student
ON student_assessment_reports(student_id, completed_at DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_student_assessment_reports_class_student
ON student_assessment_reports(class_id, student_id, completed_at DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_student_assessment_reports_source
ON student_assessment_reports(source_table, source_session_id);

CREATE TABLE IF NOT EXISTS class_assessment_report_prompt_settings (
  class_id text PRIMARY KEY REFERENCES classes(id) ON DELETE CASCADE,
  value jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
"""

_VARIABLE_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _model_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model)


def ensure_report_tables(session: Any) -> None:
    session.connection().exec_driver_sql(_CREATE_REPORT_TABLES_SQL)


def _settings_from_value(value: Any) -> AssessmentReportPromptSettings:
    payload = value if isinstance(value, dict) else {}
    return AssessmentReportPromptSettings(
        summary_prompt=str(payload.get("summary_prompt") or DEFAULT_SUMMARY_PROMPT),
        mistake_prompt=str(payload.get("mistake_prompt") or DEFAULT_MISTAKE_PROMPT),
    )


def default_report_prompt_settings() -> AssessmentReportPromptSettings:
    return AssessmentReportPromptSettings(summary_prompt=DEFAULT_SUMMARY_PROMPT, mistake_prompt=DEFAULT_MISTAKE_PROMPT)


def _validate_prompt_template(prompt: str) -> None:
    variables = set(_VARIABLE_PATTERN.findall(prompt or ""))
    unsupported = sorted(variables - set(SUPPORTED_PROMPT_VARIABLES))
    if unsupported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Unsupported report prompt variables", "unsupported_variables": unsupported},
        )


def _validate_prompt_settings(settings: AssessmentReportPromptSettingsUpdate | AssessmentReportPromptSettings) -> None:
    _validate_prompt_template(settings.summary_prompt)
    _validate_prompt_template(settings.mistake_prompt)


def get_global_report_prompt_settings(user: Any | None = None) -> AssessmentReportPromptSettingsResponse:
    settings = _settings_from_value(_load_setting_value(REPORT_PROMPT_SETTINGS_KEY))
    return AssessmentReportPromptSettingsResponse(
        settings=settings,
        source="global",
        has_override=False,
        supported_variables=list(SUPPORTED_PROMPT_VARIABLES),
        can_edit=bool(user and str(getattr(user, "role", "")) == "admin"),
    )


def save_global_report_prompt_settings(
    payload: AssessmentReportPromptSettingsUpdate,
    user: Any,
) -> AssessmentReportPromptSettingsResponse:
    if str(getattr(user, "role", "")) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can edit global report prompts")
    _validate_prompt_settings(payload)
    saved = _save_setting_value(
        REPORT_PROMPT_SETTINGS_KEY,
        _model_dump(AssessmentReportPromptSettings(summary_prompt=payload.summary_prompt, mistake_prompt=payload.mistake_prompt)),
        user.id,
    )
    return AssessmentReportPromptSettingsResponse(
        settings=_settings_from_value(saved),
        source="global",
        has_override=False,
        supported_variables=list(SUPPORTED_PROMPT_VARIABLES),
        can_edit=True,
    )


def reset_global_report_prompt_settings(user: Any) -> AssessmentReportPromptSettingsResponse:
    if str(getattr(user, "role", "")) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can edit global report prompts")
    saved = _save_setting_value(REPORT_PROMPT_SETTINGS_KEY, _model_dump(default_report_prompt_settings()), user.id)
    return AssessmentReportPromptSettingsResponse(
        settings=_settings_from_value(saved),
        source="global",
        has_override=False,
        supported_variables=list(SUPPORTED_PROMPT_VARIABLES),
        can_edit=True,
    )


def _load_class_prompt_value(session: Any, class_id: str) -> dict[str, Any] | None:
    ensure_report_tables(session)
    row = (
        session.execute(
            text("SELECT value FROM class_assessment_report_prompt_settings WHERE class_id = :class_id"),
            {"class_id": class_id},
        )
        .mappings()
        .first()
    )
    return dict(row["value"] or {}) if row else None


def get_class_report_prompt_settings(class_id: str, user: Any) -> AssessmentReportPromptSettingsResponse:
    require_class_access(class_id, user)
    inherited = _settings_from_value(_load_setting_value(REPORT_PROMPT_SETTINGS_KEY))
    with db_session() as session:
        value = _load_class_prompt_value(session, class_id)
    if value is None:
        return AssessmentReportPromptSettingsResponse(
            settings=inherited,
            inherited_settings=inherited,
            source="global",
            has_override=False,
            supported_variables=list(SUPPORTED_PROMPT_VARIABLES),
            can_edit=True,
        )
    return AssessmentReportPromptSettingsResponse(
        settings=_settings_from_value(value),
        inherited_settings=inherited,
        source="class",
        has_override=True,
        supported_variables=list(SUPPORTED_PROMPT_VARIABLES),
        can_edit=True,
    )


def update_class_report_prompt_settings(
    payload: AssessmentReportPromptSettingsUpdate,
    class_id: str,
    user: Any,
) -> AssessmentReportPromptSettingsResponse:
    require_class_access(class_id, user)
    _validate_prompt_settings(payload)
    value = _model_dump(AssessmentReportPromptSettings(summary_prompt=payload.summary_prompt, mistake_prompt=payload.mistake_prompt))
    with db_session() as session:
        ensure_report_tables(session)
        session.execute(
            text(
                """
                INSERT INTO class_assessment_report_prompt_settings (class_id, value, updated_by)
                VALUES (:class_id, CAST(:value AS jsonb), CAST(:updated_by AS uuid))
                ON CONFLICT (class_id) DO UPDATE SET
                  value = EXCLUDED.value,
                  updated_by = EXCLUDED.updated_by,
                  updated_at = now()
                """
            ),
            {"class_id": class_id, "value": _json(value), "updated_by": user.id},
        )
    return get_class_report_prompt_settings(class_id, user)


def clear_class_report_prompt_settings(class_id: str, user: Any) -> AssessmentReportPromptSettingsResponse:
    require_class_access(class_id, user)
    with db_session() as session:
        ensure_report_tables(session)
        session.execute(
            text("DELETE FROM class_assessment_report_prompt_settings WHERE class_id = :class_id"),
            {"class_id": class_id},
        )
    return get_class_report_prompt_settings(class_id, user)


def _effective_prompt_settings(class_id: str | None) -> tuple[AssessmentReportPromptSettings, str]:
    inherited = _settings_from_value(_load_setting_value(REPORT_PROMPT_SETTINGS_KEY))
    if not class_id:
        return inherited, "global"
    with db_session() as session:
        value = _load_class_prompt_value(session, class_id)
    if value is None:
        return inherited, "global"
    return _settings_from_value(value), "class"


def _render_prompt(prompt: str, variables: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        return str(variables.get(name, ""))

    return _VARIABLE_PATTERN.sub(replace, prompt)


def _safe_percent(value: float) -> str:
    return f"{round(value * 100, 1)}%"


def _compact_json(value: Any) -> str:
    if value in (None, "", [], {}):
        return "无"
    return json.dumps(value, ensure_ascii=False, default=str)


def _answer_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def _correct_answer(row: dict[str, Any]) -> Any:
    answer = row.get("answer") if isinstance(row.get("answer"), dict) else {}
    question_type = str(row.get("question_type") or "")
    if question_type in {"single_choice", "true_false"}:
        return answer.get("value")
    if question_type == "fill_blank":
        return answer.get("accepted_answers") or []
    return answer


def _generated_text(text_value: str, *, source: str = "fallback", mode: str = "fallback") -> AssessmentReportGeneratedText:
    return AssessmentReportGeneratedText(
        text=text_value,
        source="ai" if source == "ai" else "fallback",
        mode=mode or "fallback",
        generated_at=datetime.now(timezone.utc),
    )


def _fallback_summary(context: dict[str, Any]) -> str:
    wrong_count = int(context.get("wrong_count") or 0)
    advice = "后续复习可优先回看错题涉及的实验现象、判断依据和点位说明。" if wrong_count else "本次测评未出现错题，可继续按当前学习计划推进。"
    return (
        f"{context.get('assessment_type', '本次测评')}已完成，得分 {context.get('score', 0)}，"
        f"正确 {context.get('correct_count', 0)}/{context.get('total_count', 0)} 题，"
        f"正确率 {context.get('correct_rate', '0%')}。{advice}"
    )


def _fallback_mistake_explanation(context: dict[str, Any], wrong_answers: list[dict[str, Any]]) -> str:
    if not wrong_answers:
        return "本次测评没有错题。"
    lines = ["本次错题可按以下思路复盘："]
    for index, item in enumerate(wrong_answers, start=1):
        lines.append(
            f"{index}. {item.get('stem') or '题目'}；作答为 {item.get('submitted_answer') or '未作答'}，"
            f"参考答案为 {item.get('correct_answer') or '未提供'}。"
            f"{' ' + str(item.get('explanation')) if item.get('explanation') else ''}"
        )
    lines.append("后续复习应把题目现象、反应条件、干扰项和对应点位说明放在一起对照。")
    return "\n".join(lines)


def _ai_ready() -> bool:
    learning = get_learning_behavior_settings()
    if not learning.learning_features.ai_assistant_enabled:
        return False
    ai_config = get_ai_configuration_response(can_edit=False, auto_check=False)
    if not ai_config.enabled_features.student_learning_analytics:
        return False
    settings = effective_ai_settings(get_settings())
    return bool(
        settings.agent_llm_provider in {"openai", "openai_compatible"}
        and settings.agent_llm_api_key
        and settings.agent_llm_model
    )


async def _generate_with_agent(
    *,
    user: Any,
    prompt: str,
    context: dict[str, Any],
    attempts: list[dict[str, Any]],
    fallback_text: str,
) -> AssessmentReportGeneratedText:
    if not _ai_ready():
        return _generated_text(fallback_text, mode="local_fallback")
    chapter_ids = [
        str(chapter_id)
        for item in attempts
        for chapter_id in _as_list(item.get("related_chapter_ids"))
        if str(chapter_id).strip()
    ]
    kp_ids = sorted(
        {
            str(kp_id)
            for item in attempts
            for kp_id in _as_list(item.get("related_knowledge_point_ids"))
            if str(kp_id).strip()
        }
    )
    experiment_id = str(attempts[0].get("experiment_id")) if attempts else None
    request = AgentAskRequest(
        student_id=str(context.get("student_id") or getattr(user, "student_id", "") or getattr(user, "username", "")),
        user_id=user.id,
        user_role="student",
        question=json.dumps({"task": prompt, "assessment_report_context": context}, ensure_ascii=False),
        chapter_id=chapter_ids[0] if chapter_ids else None,
        experiment_id=experiment_id,
        knowledge_point_ids=kp_ids,
        allow_progress_lookup=True,
        allow_rag_lookup=True,
        assessment_review=True,
        max_answer_chars=1800,
    )
    try:
        response = await run_agent(request, settings=effective_ai_settings(get_settings()))
    except Exception:
        return _generated_text(fallback_text, mode="agent_error_fallback")
    if not response.answer or response.mode in {"guardrail_refusal", "guardrail_hint"}:
        return _generated_text(fallback_text, mode=response.mode or "agent_guardrail_fallback")
    return _generated_text(response.answer, source="ai", mode=response.mode)


def _report_type_label(report_type: str) -> str:
    return {
        "pretest": "课前测试",
        "smart": "智能测试",
        "custom": "自主测试",
        "point": "点位测评",
        "posttest": "课后测试",
    }.get(report_type, "测评")


def _report_title(report_type: str) -> str:
    return f"{_report_type_label(report_type)}报告"


def _context_variables(
    *,
    user: Any,
    report_type: str,
    score: float,
    correct_count: int,
    total_count: int,
    correct_rate: float,
    wrong_answers: list[dict[str, Any]],
    payload: dict[str, Any],
) -> dict[str, Any]:
    experiments = payload.get("experiments") if isinstance(payload.get("experiments"), list) else []
    points = [
        point
        for experiment in experiments
        if isinstance(experiment, dict)
        for point in _as_list(experiment.get("points"))
        if isinstance(point, dict)
    ]
    experiment_points = [
        point.get("title") or point.get("id")
        for point in points
        if point.get("title") or point.get("id")
    ] or [item.get("title") or item.get("id") for item in experiments if isinstance(item, dict) and (item.get("title") or item.get("id"))]
    variables = {
        "student_name": getattr(user, "display_name", "") or getattr(user, "student_id", "") or getattr(user, "username", ""),
        "student_id": getattr(user, "student_id", None) or getattr(user, "username", ""),
        "assessment_type": _report_type_label(report_type),
        "score": f"{round(score, 1)}",
        "correct_count": correct_count,
        "total_count": total_count,
        "correct_rate": _safe_percent(correct_rate),
        "wrong_count": len(wrong_answers),
        "wrong_questions": _compact_json(wrong_answers),
        "mastery_changes": _compact_json(payload.get("mastery_changes")),
        "experiment_points": "、".join(str(item) for item in experiment_points[:12]) or "无",
    }
    return variables


async def _generate_report_texts(
    *,
    user: Any,
    class_id: str | None,
    report_type: str,
    score: float,
    correct_count: int,
    total_count: int,
    correct_rate: float,
    wrong_answers: list[dict[str, Any]],
    payload: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> tuple[AssessmentReportGeneratedText, AssessmentReportGeneratedText, dict[str, Any]]:
    settings, prompt_source = _effective_prompt_settings(class_id)
    variables = _context_variables(
        user=user,
        report_type=report_type,
        score=score,
        correct_count=correct_count,
        total_count=total_count,
        correct_rate=correct_rate,
        wrong_answers=wrong_answers,
        payload=payload,
    )
    context = {**variables, "report_type": report_type, "payload": payload}
    summary_prompt = _render_prompt(settings.summary_prompt, variables)
    mistake_prompt = _render_prompt(settings.mistake_prompt, variables)
    summary = await _generate_with_agent(
        user=user,
        prompt=summary_prompt,
        context=context,
        attempts=attempts,
        fallback_text=_fallback_summary(context),
    )
    if wrong_answers:
        mistake = await _generate_with_agent(
            user=user,
            prompt=mistake_prompt,
            context=context,
            attempts=attempts,
            fallback_text=_fallback_mistake_explanation(context, wrong_answers),
        )
    else:
        mistake = _generated_text("本次测评没有错题。", mode="no_wrong_answers")
    prompt_snapshot = {
        "source": prompt_source,
        "summary_prompt": settings.summary_prompt,
        "mistake_prompt": settings.mistake_prompt,
        "supported_variables": list(SUPPORTED_PROMPT_VARIABLES),
    }
    return summary, mistake, prompt_snapshot


def _summary_from_row(row: dict[str, Any]) -> StudentAssessmentReportSummary:
    return StudentAssessmentReportSummary(
        id=str(row["id"]),
        student_id=str(row["student_id"]),
        class_id=str(row["class_id"]) if row.get("class_id") else None,
        report_type=str(row["report_type"]),  # type: ignore[arg-type]
        source_session_id=str(row["source_session_id"]),
        title=str(row["title"]),
        score=float(row.get("score") or 0),
        correct_count=int(row.get("correct_count") or 0),
        total_count=int(row.get("total_count") or 0),
        correct_rate=float(row.get("correct_rate") or 0),
        wrong_count=int(row.get("wrong_count") or 0),
        completed_at=row["completed_at"],
    )


def _report_from_row(row: dict[str, Any]) -> StudentAssessmentReport:
    summary = _summary_from_row(row)
    return StudentAssessmentReport(
        **_model_dump(summary),
        summary=AssessmentReportGeneratedText(**(row.get("summary") if isinstance(row.get("summary"), dict) else {})),
        mistake_explanation=AssessmentReportGeneratedText(
            **(row.get("mistake_explanation") if isinstance(row.get("mistake_explanation"), dict) else {})
        ),
        prompt_snapshot=row.get("prompt_snapshot") if isinstance(row.get("prompt_snapshot"), dict) else {},
        payload=row.get("payload") if isinstance(row.get("payload"), dict) else {},
    )


def _insert_report(
    *,
    student_id: str,
    class_id: str | None,
    report_type: str,
    source_session_id: str,
    source_table: str,
    title: str,
    score: float,
    correct_count: int,
    total_count: int,
    correct_rate: float,
    wrong_count: int,
    summary: AssessmentReportGeneratedText,
    mistake_explanation: AssessmentReportGeneratedText,
    prompt_snapshot: dict[str, Any],
    payload: dict[str, Any],
    completed_at: Any,
) -> StudentAssessmentReport:
    if report_type not in REPORT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported report type")
    with db_session() as session:
        ensure_report_tables(session)
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO student_assessment_reports (
                      student_id, class_id, report_type, source_session_id, source_table,
                      title, score, correct_count, total_count, correct_rate, wrong_count,
                      summary, mistake_explanation, prompt_snapshot, payload, completed_at
                    )
                    VALUES (
                      :student_id, :class_id, :report_type, CAST(:source_session_id AS uuid), :source_table,
                      :title, :score, :correct_count, :total_count, :correct_rate, :wrong_count,
                      CAST(:summary AS jsonb), CAST(:mistake_explanation AS jsonb),
                      CAST(:prompt_snapshot AS jsonb), CAST(:payload AS jsonb), :completed_at
                    )
                    ON CONFLICT (report_type, source_session_id) DO UPDATE SET
                      title = EXCLUDED.title,
                      score = EXCLUDED.score,
                      correct_count = EXCLUDED.correct_count,
                      total_count = EXCLUDED.total_count,
                      correct_rate = EXCLUDED.correct_rate,
                      wrong_count = EXCLUDED.wrong_count,
                      summary = EXCLUDED.summary,
                      mistake_explanation = EXCLUDED.mistake_explanation,
                      prompt_snapshot = EXCLUDED.prompt_snapshot,
                      payload = EXCLUDED.payload,
                      completed_at = EXCLUDED.completed_at,
                      updated_at = now()
                    RETURNING *
                    """
                ),
                {
                    "student_id": student_id,
                    "class_id": class_id,
                    "report_type": report_type,
                    "source_session_id": source_session_id,
                    "source_table": source_table,
                    "title": title,
                    "score": score,
                    "correct_count": correct_count,
                    "total_count": total_count,
                    "correct_rate": correct_rate,
                    "wrong_count": wrong_count,
                    "summary": _json(_model_dump(summary)),
                    "mistake_explanation": _json(_model_dump(mistake_explanation)),
                    "prompt_snapshot": _json(prompt_snapshot),
                    "payload": _json(payload),
                    "completed_at": completed_at or datetime.now(timezone.utc),
                },
            )
            .mappings()
            .one()
        )
    return _report_from_row(dict(row))


def _load_pretest_attempts(session: Any, *, student_id: str, session_id: str) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT a.question_id::text AS question_id,
                       a.correct,
                       a.submitted_answer,
                       a.metadata,
                       q.experiment_id,
                       fe.title AS experiment_title,
                       q.question_type,
                       q.stem,
                       q.options,
                       q.answer,
                       q.explanation,
                       q.difficulty,
                       q.related_chapter_ids,
                       q.related_knowledge_point_ids
                FROM experiment_question_attempts a
                JOIN experiment_questions q ON q.id = a.question_id
                JOIN formal_experiments fe ON fe.id = q.experiment_id
                WHERE a.student_id = :student_id
                  AND a.metadata->>'pretest_session_id' = :session_id
                ORDER BY a.created_at, a.id
                """
            ),
            {"student_id": student_id, "session_id": session_id},
        )
        .mappings()
        .all()
    ]


def _shape_attempt(row: dict[str, Any]) -> dict[str, Any]:
    submitted = _answer_value((row.get("submitted_answer") or {}).get("value") if isinstance(row.get("submitted_answer"), dict) else row.get("submitted_answer"))
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    return {
        "question_id": str(row.get("question_id") or ""),
        "experiment_id": str(row.get("experiment_id") or ""),
        "experiment_title": str(row.get("experiment_title") or ""),
        "question_type": str(row.get("question_type") or ""),
        "stem": str(row.get("stem") or ""),
        "options": row.get("options") if isinstance(row.get("options"), list) else [],
        "submitted_answer": submitted,
        "correct_answer": _correct_answer(row),
        "correct": bool(row.get("correct")),
        "explanation": row.get("explanation"),
        "area": metadata.get("area"),
        "stage": metadata.get("pretest_stage"),
        "related_chapter_ids": _as_list(row.get("related_chapter_ids")),
        "related_knowledge_point_ids": _as_list(row.get("related_knowledge_point_ids")),
    }


async def create_pretest_report(user: Any, session_id: str) -> StudentAssessmentReport:
    student_id = str(getattr(user, "student_id", None) or getattr(user, "username", "")).strip().upper()
    with db_session() as session:
        ensure_report_tables(session)
        session_row = (
            session.execute(
                text(
                    """
                    SELECT *
                    FROM student_pretest_sessions
                    WHERE id = CAST(:session_id AS uuid)
                      AND student_id = :student_id
                      AND status = 'completed'
                    """
                ),
                {"session_id": session_id, "student_id": student_id},
            )
            .mappings()
            .first()
        )
        if not session_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pretest session not found")
        attempts = _load_pretest_attempts(session, student_id=student_id, session_id=session_id)
    shaped_attempts = [_shape_attempt(row) for row in attempts]
    total_count = len(shaped_attempts)
    correct_count = sum(1 for item in shaped_attempts if item["correct"])
    score = round(100 * correct_count / total_count, 2) if total_count else 0.0
    correct_rate = round(correct_count / total_count, 4) if total_count else 0.0
    experiments: dict[str, dict[str, Any]] = {}
    for item in shaped_attempts:
        experiment_id = str(item.get("experiment_id") or "")
        if experiment_id:
            experiments.setdefault(experiment_id, {"id": experiment_id, "title": item.get("experiment_title")})
    wrong_answers = [item for item in shaped_attempts if not item["correct"]]
    payload = {
        "assessment_mode": "pretest",
        "experiments": list(experiments.values()),
        "questions": shaped_attempts,
        "wrong_answers": wrong_answers,
        "mastery_changes": [],
        "weakest_area": dict(session_row).get("weakest_area"),
    }
    summary, mistake, prompt_snapshot = await _generate_report_texts(
        user=user,
        class_id=dict(session_row).get("class_id"),
        report_type="pretest",
        score=score,
        correct_count=correct_count,
        total_count=total_count,
        correct_rate=correct_rate,
        wrong_answers=wrong_answers,
        payload=payload,
        attempts=shaped_attempts,
    )
    return _insert_report(
        student_id=student_id,
        class_id=dict(session_row).get("class_id"),
        report_type="pretest",
        source_session_id=session_id,
        source_table="student_pretest_sessions",
        title=_report_title("pretest"),
        score=score,
        correct_count=correct_count,
        total_count=total_count,
        correct_rate=correct_rate,
        wrong_count=len(wrong_answers),
        summary=summary,
        mistake_explanation=mistake,
        prompt_snapshot=prompt_snapshot,
        payload=payload,
        completed_at=dict(session_row).get("completed_at"),
    )


def _load_smart_attempts(session: Any, *, student_id: str, session_id: str) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT a.question_id::text AS question_id,
                       a.correct,
                       a.submitted_answer,
                       a.metadata,
                       q.experiment_id,
                       fe.title AS experiment_title,
                       q.question_type,
                       q.stem,
                       q.options,
                       q.answer,
                       q.explanation,
                       q.difficulty,
                       q.related_chapter_ids,
                       q.related_knowledge_point_ids
                FROM experiment_question_attempts a
                JOIN experiment_questions q ON q.id = a.question_id
                JOIN formal_experiments fe ON fe.id = q.experiment_id
                WHERE a.student_id = :student_id
                  AND a.metadata->>'smart_assessment_session_id' = :session_id
                ORDER BY a.created_at, a.id
                """
            ),
            {"student_id": student_id, "session_id": session_id},
        )
        .mappings()
        .all()
    ]


async def create_smart_assessment_report(user: Any, report: StudentSmartAssessmentReport) -> StudentAssessmentReport:
    session_id = report.session_id
    student_id = str(getattr(user, "student_id", None) or getattr(user, "username", "")).strip().upper()
    report_type = str(report.assessment_mode or "smart")
    if report_type not in {"smart", "custom", "point"}:
        report_type = "smart"
    with db_session() as session:
        ensure_report_tables(session)
        session_row = (
            session.execute(
                text(
                    """
                    SELECT *
                    FROM student_smart_assessment_sessions
                    WHERE id = CAST(:session_id AS uuid)
                      AND student_id = :student_id
                      AND status = 'completed'
                    """
                ),
                {"session_id": session_id, "student_id": student_id},
            )
            .mappings()
            .first()
        )
        if not session_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment session not found")
        attempts = _load_smart_attempts(session, student_id=student_id, session_id=session_id)
    payload = _model_dump(report)
    wrong_answers = payload.get("wrong_answers") if isinstance(payload.get("wrong_answers"), list) else []
    shaped_attempts = [_shape_attempt(row) for row in attempts]
    summary, mistake, prompt_snapshot = await _generate_report_texts(
        user=user,
        class_id=dict(session_row).get("class_id"),
        report_type=report_type,
        score=float(report.score),
        correct_count=int(report.correct_count),
        total_count=int(report.total_count),
        correct_rate=float(report.correct_rate),
        wrong_answers=[item for item in wrong_answers if isinstance(item, dict)],
        payload=payload,
        attempts=shaped_attempts,
    )
    return _insert_report(
        student_id=student_id,
        class_id=dict(session_row).get("class_id"),
        report_type=report_type,
        source_session_id=session_id,
        source_table="student_smart_assessment_sessions",
        title=_report_title(report_type),
        score=float(report.score),
        correct_count=int(report.correct_count),
        total_count=int(report.total_count),
        correct_rate=float(report.correct_rate),
        wrong_count=len(wrong_answers),
        summary=summary,
        mistake_explanation=mistake,
        prompt_snapshot=prompt_snapshot,
        payload=payload,
        completed_at=dict(session_row).get("completed_at"),
    )


def list_student_assessment_reports(user: Any) -> StudentAssessmentReportListResponse:
    student_id = str(getattr(user, "student_id", None) or getattr(user, "username", "")).strip().upper()
    with db_session() as session:
        ensure_report_tables(session)
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT *
                    FROM student_assessment_reports
                    WHERE student_id = :student_id
                    ORDER BY completed_at DESC, created_at DESC
                    LIMIT 200
                    """
                ),
                {"student_id": student_id},
            )
            .mappings()
            .all()
        ]
    return StudentAssessmentReportListResponse(reports=[_summary_from_row(row) for row in rows])


def get_student_assessment_report(report_id: str, user: Any) -> StudentAssessmentReport:
    student_id = str(getattr(user, "student_id", None) or getattr(user, "username", "")).strip().upper()
    with db_session() as session:
        ensure_report_tables(session)
        row = (
            session.execute(
                text(
                    """
                    SELECT *
                    FROM student_assessment_reports
                    WHERE id = CAST(:report_id AS uuid)
                      AND student_id = :student_id
                    """
                ),
                {"report_id": report_id, "student_id": student_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return _report_from_row(dict(row))


def list_teacher_student_assessment_reports(class_id: str, student_id: str, user: Any) -> StudentAssessmentReportListResponse:
    require_class_access(class_id, user)
    with db_session() as session:
        ensure_report_tables(session)
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT *
                    FROM student_assessment_reports
                    WHERE class_id = :class_id
                      AND student_id = :student_id
                    ORDER BY completed_at DESC, created_at DESC
                    LIMIT 200
                    """
                ),
                {"class_id": class_id, "student_id": student_id.strip().upper()},
            )
            .mappings()
            .all()
        ]
    return StudentAssessmentReportListResponse(reports=[_summary_from_row(row) for row in rows])


def get_teacher_student_assessment_report(class_id: str, student_id: str, report_id: str, user: Any) -> StudentAssessmentReport:
    require_class_access(class_id, user)
    with db_session() as session:
        ensure_report_tables(session)
        row = (
            session.execute(
                text(
                    """
                    SELECT *
                    FROM student_assessment_reports
                    WHERE id = CAST(:report_id AS uuid)
                      AND class_id = :class_id
                      AND student_id = :student_id
                    """
                ),
                {"report_id": report_id, "class_id": class_id, "student_id": student_id.strip().upper()},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return _report_from_row(dict(row))
