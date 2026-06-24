from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import replace
from typing import Any

from sqlalchemy import text

from server.app.domains.assessments.mastery import ensure_student_point_mastery_table, update_point_mastery_from_attempt_rows
from server.app.domains.assessments.posttest import (
    PosttestQuestionCandidate,
    _answer_key,
    _as_list,
    _experiment_summary_from_row,
    _json,
    _json_array,
    _load_experiment_summaries,
    _load_questions_by_ids,
    _mastery_average,
    _mastery_changes,
    _question_canonical_point_ids,
    _question_ids,
    _question_point_node_ids,
    _question_source_placement_node_ids,
    _session_experiment_ids,
    _session_question_ids,
    _stable_hash,
)
from server.app.domains.assessments.pretest import _ensure_student_row, _load_student_context
from server.app.domains.assessments.student_experiment import _grade_answer
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.domains.platform.settings import CustomAssessmentSettings, SmartAssessmentSettings, get_learning_behavior_settings
from server.app.domains.roster.classes import require_class_access
from server.app.infrastructure.database import db_session
from server.app.mastery import update_mastery
from server.app.student_smart_assessment_schemas import (
    CustomAssessmentExperimentOption,
    CustomAssessmentOptionsSettings,
    CustomAssessmentSettingsResponse,
    PublicSmartAssessmentQuestion,
    StudentAssessmentStatusResponse,
    StudentCustomAssessmentOptionsResponse,
    StudentCustomAssessmentStartRequest,
    StudentPointAssessmentStartRequest,
    SmartAssessmentClassPreviewExperiment,
    SmartAssessmentClassPreviewResponse,
    SmartAssessmentCompositionSummary,
    SmartAssessmentExperimentSummary,
    SmartAssessmentPointSummary,
    SmartAssessmentStrategyResponse,
    StudentSmartAssessmentReport,
    StudentSmartAssessmentResponse,
    StudentSmartAssessmentSubmitRequest,
    StudentSmartAssessmentSubmitResponse,
    StudentSmartAssessmentWrongAnswer,
)

CUSTOM_QUESTION_COUNT_OPTIONS = [5, 10, 15, 20]
POINT_ASSESSMENT_TARGET_COUNT = 3
SMART_BASELINE_PROMPT_DISMISSED_EVENT = "smart_baseline_prompt_dismissed"
ASSESSMENT_SOURCE_VALUES = {"measured", "untested", "custom", "point"}

_CREATE_SMART_ASSESSMENT_SQL = """
CREATE TABLE IF NOT EXISTS student_smart_assessment_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id text NOT NULL,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  status text NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),
  assessment_mode text NOT NULL DEFAULT 'smart',
  strategy_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
  composition_summary jsonb NOT NULL DEFAULT '{}'::jsonb,
  experiment_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  point_node_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  canonical_point_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  source_placement_node_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  question_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  mastery_before jsonb NOT NULL DEFAULT '{}'::jsonb,
  mastery_after jsonb NOT NULL DEFAULT '{}'::jsonb,
  report jsonb NOT NULL DEFAULT '{}'::jsonb,
  score numeric,
  correct_count int,
  total_count int,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_student_smart_assessment_sessions_open
ON student_smart_assessment_sessions(student_id)
WHERE status = 'in_progress';

CREATE INDEX IF NOT EXISTS idx_student_smart_assessment_sessions_student
ON student_smart_assessment_sessions(student_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_student_smart_assessment_sessions_class
ON student_smart_assessment_sessions(class_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_student_smart_assessment_sessions_mode
ON student_smart_assessment_sessions(assessment_mode, status, created_at DESC);

CREATE TABLE IF NOT EXISTS class_smart_assessment_settings (
  class_id text PRIMARY KEY REFERENCES classes(id) ON DELETE CASCADE,
  value jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS class_custom_assessment_settings (
  class_id text PRIMARY KEY REFERENCES classes(id) ON DELETE CASCADE,
  value jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
"""


def _ensure_tables(session: Any) -> None:
    session.connection().exec_driver_sql(_CREATE_SMART_ASSESSMENT_SQL)
    ensure_student_point_mastery_table(session)
    session.execute(text("ALTER TABLE student_smart_assessment_sessions ADD COLUMN IF NOT EXISTS assessment_mode text NOT NULL DEFAULT 'smart'"))
    session.execute(text("ALTER TABLE student_smart_assessment_sessions ADD COLUMN IF NOT EXISTS point_node_ids jsonb NOT NULL DEFAULT '[]'::jsonb"))
    session.execute(text("ALTER TABLE student_smart_assessment_sessions ADD COLUMN IF NOT EXISTS canonical_point_ids jsonb NOT NULL DEFAULT '[]'::jsonb"))
    session.execute(text("ALTER TABLE student_smart_assessment_sessions ADD COLUMN IF NOT EXISTS source_placement_node_ids jsonb NOT NULL DEFAULT '[]'::jsonb"))


def _model_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _strategy_from_value(value: Any, fallback: SmartAssessmentSettings | None = None) -> SmartAssessmentSettings:
    base = _model_dump(fallback or SmartAssessmentSettings())
    if isinstance(value, dict):
        base.update(value)
    return SmartAssessmentSettings(**base)


def _custom_settings_from_value(value: Any, fallback: CustomAssessmentSettings | None = None) -> CustomAssessmentSettings:
    base = _model_dump(fallback or CustomAssessmentSettings())
    if isinstance(value, dict):
        base.update(value)
    settings = CustomAssessmentSettings(**base)
    max_count = max(option for option in CUSTOM_QUESTION_COUNT_OPTIONS if option <= settings.max_question_count)
    default_count = settings.default_question_count
    if default_count not in CUSTOM_QUESTION_COUNT_OPTIONS or default_count > max_count:
        default_count = min((option for option in CUSTOM_QUESTION_COUNT_OPTIONS if option <= max_count), key=lambda option: abs(option - max_count))
    return CustomAssessmentSettings(
        enabled=settings.enabled,
        default_question_count=default_count,
        max_question_count=max_count,
        max_questions_per_experiment=settings.max_questions_per_experiment,
    )


def _custom_options_settings(settings: CustomAssessmentSettings) -> CustomAssessmentOptionsSettings:
    return CustomAssessmentOptionsSettings(
        enabled=settings.enabled,
        question_count_options=[option for option in CUSTOM_QUESTION_COUNT_OPTIONS if option <= settings.max_question_count],
        default_question_count=settings.default_question_count,
        max_question_count=settings.max_question_count,
        max_questions_per_experiment=settings.max_questions_per_experiment,
    )


def _load_class_strategy_override(session: Any, class_id: str | None) -> dict[str, Any] | None:
    if not class_id:
        return None
    _ensure_tables(session)
    row = (
        session.execute(
            text("SELECT value FROM class_smart_assessment_settings WHERE class_id = :class_id"),
            {"class_id": class_id},
        )
        .mappings()
        .first()
    )
    if not row or not isinstance(row.get("value"), dict):
        return None
    return dict(row["value"])


def _effective_strategy(session: Any, class_id: str | None) -> tuple[SmartAssessmentSettings, SmartAssessmentSettings, bool]:
    inherited = get_learning_behavior_settings().assessment.smart_assessment
    override = _load_class_strategy_override(session, class_id)
    if override is None:
        return inherited, inherited, False
    return _strategy_from_value(override, inherited), inherited, True


def _load_class_custom_override(session: Any, class_id: str | None) -> dict[str, Any] | None:
    if not class_id:
        return None
    _ensure_tables(session)
    row = (
        session.execute(
            text("SELECT value FROM class_custom_assessment_settings WHERE class_id = :class_id"),
            {"class_id": class_id},
        )
        .mappings()
        .first()
    )
    if not row or not isinstance(row.get("value"), dict):
        return None
    return dict(row["value"])


def _effective_custom_settings(session: Any, class_id: str | None) -> tuple[CustomAssessmentSettings, CustomAssessmentSettings, bool]:
    inherited = get_learning_behavior_settings().assessment.custom_assessment
    override = _load_class_custom_override(session, class_id)
    if override is None:
        inherited = _custom_settings_from_value(_model_dump(inherited))
        return inherited, inherited, False
    inherited = _custom_settings_from_value(_model_dump(inherited))
    return _custom_settings_from_value(override, inherited), inherited, True


def _ensure_class_exists(session: Any, class_id: str) -> None:
    row = session.execute(text("SELECT id FROM classes WHERE id = :class_id"), {"class_id": class_id}).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")


def get_class_smart_assessment_strategy(class_id: str, user: Any) -> SmartAssessmentStrategyResponse:
    require_class_access(class_id, user)
    with db_session() as session:
        _ensure_tables(session)
        _ensure_class_exists(session, class_id)
        strategy, inherited, has_override = _effective_strategy(session, class_id)
    return SmartAssessmentStrategyResponse(
        strategy=strategy,
        inherited_strategy=inherited,
        source="class" if has_override else "system_default",
        has_override=has_override,
        can_edit=True,
    )


def update_class_smart_assessment_strategy(
    payload: SmartAssessmentSettings,
    class_id: str,
    user: Any,
) -> SmartAssessmentStrategyResponse:
    require_class_access(class_id, user)
    with db_session() as session:
        _ensure_tables(session)
        _ensure_class_exists(session, class_id)
        inherited = get_learning_behavior_settings().assessment.smart_assessment
        strategy = _strategy_from_value(_model_dump(payload), inherited)
        session.execute(
            text(
                """
                INSERT INTO class_smart_assessment_settings (class_id, value, updated_by, updated_at)
                VALUES (:class_id, CAST(:value AS jsonb), CAST(:updated_by AS uuid), now())
                ON CONFLICT (class_id) DO UPDATE SET
                  value = EXCLUDED.value,
                  updated_by = EXCLUDED.updated_by,
                  updated_at = now()
                """
            ),
            {"class_id": class_id, "value": _json(_model_dump(strategy)), "updated_by": user.id},
        )
    return SmartAssessmentStrategyResponse(
        strategy=strategy,
        inherited_strategy=inherited,
        source="class",
        has_override=True,
        can_edit=True,
    )


def clear_class_smart_assessment_strategy(class_id: str, user: Any) -> SmartAssessmentStrategyResponse:
    require_class_access(class_id, user)
    with db_session() as session:
        _ensure_tables(session)
        _ensure_class_exists(session, class_id)
        session.execute(
            text("DELETE FROM class_smart_assessment_settings WHERE class_id = :class_id"),
            {"class_id": class_id},
        )
        inherited = get_learning_behavior_settings().assessment.smart_assessment
    return SmartAssessmentStrategyResponse(
        strategy=inherited,
        inherited_strategy=inherited,
        source="system_default",
        has_override=False,
        can_edit=True,
    )


def get_class_custom_assessment_settings(class_id: str, user: Any) -> CustomAssessmentSettingsResponse:
    require_class_access(class_id, user)
    with db_session() as session:
        _ensure_tables(session)
        _ensure_class_exists(session, class_id)
        settings, inherited, has_override = _effective_custom_settings(session, class_id)
    return CustomAssessmentSettingsResponse(
        settings=settings,
        inherited_settings=inherited,
        source="class" if has_override else "system_default",
        has_override=has_override,
        can_edit=True,
    )


def update_class_custom_assessment_settings(
    payload: CustomAssessmentSettings,
    class_id: str,
    user: Any,
) -> CustomAssessmentSettingsResponse:
    require_class_access(class_id, user)
    with db_session() as session:
        _ensure_tables(session)
        _ensure_class_exists(session, class_id)
        _current, inherited, _has_override = _effective_custom_settings(session, class_id)
        settings = _custom_settings_from_value(_model_dump(payload), inherited)
        session.execute(
            text(
                """
                INSERT INTO class_custom_assessment_settings (class_id, value, updated_by, updated_at)
                VALUES (:class_id, CAST(:value AS jsonb), CAST(:updated_by AS uuid), now())
                ON CONFLICT (class_id) DO UPDATE SET
                  value = EXCLUDED.value,
                  updated_by = EXCLUDED.updated_by,
                  updated_at = now()
                """
            ),
            {"class_id": class_id, "value": _json(_model_dump(settings)), "updated_by": user.id},
        )
    return CustomAssessmentSettingsResponse(
        settings=settings,
        inherited_settings=inherited,
        source="class",
        has_override=True,
        can_edit=True,
    )


def clear_class_custom_assessment_settings(class_id: str, user: Any) -> CustomAssessmentSettingsResponse:
    require_class_access(class_id, user)
    with db_session() as session:
        _ensure_tables(session)
        _ensure_class_exists(session, class_id)
        session.execute(
            text("DELETE FROM class_custom_assessment_settings WHERE class_id = :class_id"),
            {"class_id": class_id},
        )
        inherited = _custom_settings_from_value(_model_dump(get_learning_behavior_settings().assessment.custom_assessment))
    return CustomAssessmentSettingsResponse(
        settings=inherited,
        inherited_settings=inherited,
        source="system_default",
        has_override=False,
        can_edit=True,
    )


def _load_class_student_ids(session: Any, class_id: str) -> list[str]:
    rows = session.execute(
        text(
            """
            SELECT DISTINCT student_id
            FROM (
              SELECT re.student_id
              FROM roster_entries re
              WHERE re.class_id = :class_id
                AND re.status <> 'disabled'
              UNION
              SELECT sp.student_id
              FROM student_profiles sp
              WHERE sp.class_id = :class_id
              UNION
              SELECT COALESCE(NULLIF(s.student_id, ''), s.id) AS student_id
              FROM students s
              WHERE s.class_id = :class_id
                AND COALESCE(s.status, 'active') <> 'disabled'
            ) class_students
            WHERE student_id IS NOT NULL
              AND btrim(student_id) <> ''
            """
        ),
        {"class_id": class_id},
    ).mappings()
    return _unique([row["student_id"] for row in rows])


def _load_class_point_mastery_map(session: Any, *, class_id: str, point_ids: list[str]) -> dict[str, dict[str, Any]]:
    point_ids = _unique(point_ids)
    if not point_ids:
        return {}
    ensure_student_point_mastery_table(session)
    rows = session.execute(
        text(
            """
            WITH class_students AS (
              SELECT DISTINCT student_id
              FROM (
                SELECT re.student_id
                FROM roster_entries re
                WHERE re.class_id = :class_id
                  AND re.status <> 'disabled'
                UNION
                SELECT sp.student_id
                FROM student_profiles sp
                WHERE sp.class_id = :class_id
                UNION
                SELECT COALESCE(NULLIF(s.student_id, ''), s.id) AS student_id
                FROM students s
                WHERE s.class_id = :class_id
                  AND COALESCE(s.status, 'active') <> 'disabled'
              ) roster_students
              WHERE student_id IS NOT NULL
                AND btrim(student_id) <> ''
            ),
            class_mastery AS (
              SELECT DISTINCT
                spm.student_id,
                spm.point_node_id,
                spm.mastery_score,
                spm.evidence_count
              FROM student_point_mastery spm
              LEFT JOIN class_students cs ON cs.student_id = spm.student_id
              WHERE spm.point_node_id = ANY(:point_ids)
                AND (cs.student_id IS NOT NULL OR spm.class_id = :class_id)
            )
            SELECT
              point_node_id,
              AVG(mastery_score) FILTER (WHERE COALESCE(evidence_count, 0) > 0) AS mastery_score,
              SUM(COALESCE(evidence_count, 0)) AS evidence_count,
              COUNT(DISTINCT student_id) FILTER (WHERE COALESCE(evidence_count, 0) > 0) AS measured_student_count
            FROM class_mastery
            GROUP BY point_node_id
            """
        ),
        {"class_id": class_id, "point_ids": point_ids},
    ).mappings()
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        evidence_count = int(row.get("evidence_count") or 0)
        point_id = str(row["point_node_id"])
        result[point_id] = {
            "mastery_score": float(row["mastery_score"]) if row.get("mastery_score") is not None and evidence_count > 0 else None,
            "evidence_count": evidence_count,
            "measured_student_count": int(row.get("measured_student_count") or 0),
        }
    return result


def _build_class_smart_assessment_preview(
    *,
    strategy: SmartAssessmentSettings,
    source: str,
    has_override: bool,
    class_student_count: int,
    point_info: dict[str, dict[str, Any]],
    point_to_experiment: dict[str, str],
    mastery: dict[str, dict[str, Any]],
) -> SmartAssessmentClassPreviewResponse:
    point_ids = _unique([point_id for point_id in point_to_experiment if point_id in point_info])
    target_count = strategy.question_count
    untested_target = min(target_count, int(round(target_count * strategy.untested_ratio_percent / 100)))
    measured_target = target_count - untested_target
    experiments: dict[str, dict[str, Any]] = {}
    measured_point_count = 0
    untested_point_count = 0
    total_measured_tickets = 0.0

    for point_id in point_ids:
        info = point_info.get(point_id) or {}
        experiment_id = str(info.get("experiment_id") or point_to_experiment.get(point_id) or "")
        if not experiment_id:
            continue
        experiment = experiments.setdefault(
            experiment_id,
            {
                "id": experiment_id,
                "title": str(info.get("experiment_title") or experiment_id),
                "candidate_point_count": 0,
                "untested_point_count": 0,
                "measured_point_count": 0,
                "mastery_scores": [],
                "estimated_draw_tickets": 0.0,
            },
        )
        experiment["candidate_point_count"] = int(experiment.get("candidate_point_count") or 0) + 1
        state = mastery.get(point_id) if isinstance(mastery.get(point_id), dict) else None
        evidence_count = int(state.get("evidence_count") or 0) if state else 0
        mastery_score = state.get("mastery_score") if state else None
        if evidence_count <= 0 or mastery_score is None:
            untested_point_count += 1
            experiment["untested_point_count"] = int(experiment.get("untested_point_count") or 0) + 1
            continue
        measured_point_count += 1
        tickets = _draw_tickets(strategy, float(mastery_score))
        total_measured_tickets += tickets
        experiment["measured_point_count"] = int(experiment.get("measured_point_count") or 0) + 1
        experiment["estimated_draw_tickets"] = float(experiment.get("estimated_draw_tickets") or 0.0) + tickets
        experiment["mastery_scores"].append(float(mastery_score))

    experiment_rows: list[SmartAssessmentClassPreviewExperiment] = []
    for experiment in experiments.values():
        scores = [float(item) for item in experiment.get("mastery_scores", [])]
        untested_estimate = (
            untested_target * int(experiment.get("untested_point_count") or 0) / untested_point_count if untested_point_count else 0.0
        )
        measured_estimate = (
            measured_target * float(experiment.get("estimated_draw_tickets") or 0.0) / total_measured_tickets
            if total_measured_tickets
            else 0.0
        )
        raw_estimate = untested_estimate + measured_estimate
        capped_estimate = min(
            float(strategy.max_questions_per_experiment),
            float(experiment.get("candidate_point_count") or 0),
            raw_estimate,
        )
        experiment_rows.append(
            SmartAssessmentClassPreviewExperiment(
                id=str(experiment["id"]),
                title=str(experiment.get("title") or experiment["id"]),
                candidate_point_count=int(experiment.get("candidate_point_count") or 0),
                untested_point_count=int(experiment.get("untested_point_count") or 0),
                measured_point_count=int(experiment.get("measured_point_count") or 0),
                average_mastery_score=round(sum(scores) / len(scores), 2) if scores else None,
                estimated_draw_tickets=round(float(experiment.get("estimated_draw_tickets") or 0.0), 2),
                estimated_question_count=round(capped_estimate, 2),
            )
        )

    experiment_rows.sort(key=lambda item: (-item.estimated_question_count, item.title, item.id))
    candidate_point_count = len(point_ids)
    warnings = {
        "no_candidate_points": candidate_point_count == 0,
        "underfilled_by_candidate_points": candidate_point_count < target_count,
        "untested_pool_underfilled": untested_target > untested_point_count,
        "measured_pool_empty": measured_target > 0 and measured_point_count == 0,
        "experiment_cap_underfilled": len(experiments) * strategy.max_questions_per_experiment < target_count,
    }
    return SmartAssessmentClassPreviewResponse(
        strategy=strategy,
        source="class" if source == "class" else "system_default",
        has_override=has_override,
        class_student_count=class_student_count,
        candidate_point_count=candidate_point_count,
        measured_point_count=measured_point_count,
        untested_point_count=untested_point_count,
        target_question_count=target_count,
        untested_target_count=untested_target,
        measured_target_count=measured_target,
        experiments=experiment_rows,
        warnings=warnings,
    )


def get_class_smart_assessment_preview(class_id: str, user: Any) -> SmartAssessmentClassPreviewResponse:
    require_class_access(class_id, user)
    with db_session() as session:
        _ensure_tables(session)
        _ensure_class_exists(session, class_id)
        strategy, _inherited, has_override = _effective_strategy(session, class_id)
        candidates = _load_all_published_candidates(session)
        point_to_experiment = _point_experiment_map(candidates)
        point_ids = _all_candidate_point_ids(candidates)
        point_info = _load_point_info(session, point_ids, fallback_experiment_by_point=point_to_experiment)
        mastery = _load_class_point_mastery_map(session, class_id=class_id, point_ids=point_ids)
        class_student_count = len(_load_class_student_ids(session, class_id))
    return _build_class_smart_assessment_preview(
        strategy=strategy,
        source="class" if has_override else "system_default",
        has_override=has_override,
        class_student_count=class_student_count,
        point_info=point_info,
        point_to_experiment=point_to_experiment,
        mastery=mastery,
    )


def _load_open_session(session: Any, student_id: str) -> dict[str, Any] | None:
    _ensure_tables(session)
    row = (
        session.execute(
            text(
                """
                SELECT *
                FROM student_smart_assessment_sessions
                WHERE student_id = :student_id
                  AND status = 'in_progress'
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"student_id": student_id},
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


def _assessment_mode_from_value(value: Any) -> str:
    mode = str(value or "smart")
    return mode if mode in {"smart", "custom", "point"} else "smart"


def _attempt_kind_for_assessment_mode(assessment_mode: str) -> str:
    if assessment_mode == "custom":
        return "custom_assessment"
    if assessment_mode == "point":
        return "point_assessment"
    return "smart_assessment"


def _assessment_submit_event_type(assessment_mode: str) -> str:
    if assessment_mode == "custom":
        return "custom_assessment_submit"
    if assessment_mode == "point":
        return "point_assessment_submit"
    return "smart_assessment_submit"


def _session_point_node_ids(row: dict[str, Any]) -> list[str]:
    return [str(item) for item in _as_list(row.get("point_node_ids")) if str(item).strip()]


def _session_canonical_point_ids(row: dict[str, Any]) -> list[str]:
    return [str(item) for item in _as_list(row.get("canonical_point_ids")) if str(item).strip()]


def _question_assessment_point_ids(question: PosttestQuestionCandidate) -> list[str]:
    return _question_source_placement_node_ids(question) or _question_point_node_ids(question)


def _question_assessment_canonical_ids(question: PosttestQuestionCandidate) -> list[str]:
    return _question_canonical_point_ids(question)


def _public_question(question: PosttestQuestionCandidate) -> PublicSmartAssessmentQuestion:
    return PublicSmartAssessmentQuestion(
        id=question.id,
        experiment_id=question.experiment_id,
        experiment_title=question.experiment_title,
        point_node_ids=_question_assessment_point_ids(question),
        canonical_point_ids=_question_assessment_canonical_ids(question),
        question_type=question.question_type,  # type: ignore[arg-type]
        stem=question.stem,
        options=question.options,
        related_chapter_ids=question.related_chapter_ids,
        related_knowledge_point_ids=question.related_knowledge_point_ids,
    )


def _load_all_published_candidates(session: Any) -> list[PosttestQuestionCandidate]:
    rows = session.execute(
        text(
            """
            SELECT q.id::text AS id, q.experiment_id, fe.title AS experiment_title,
                   q.question_type, q.stem, q.options, q.answer, q.explanation,
                   q.difficulty, q.related_chapter_ids, q.related_knowledge_point_ids,
                   q.primary_point_node_ids, q.primary_canonical_point_ids, q.source_placement_node_ids
            FROM experiment_questions q
            JOIN formal_experiments fe ON fe.id = q.experiment_id
            WHERE q.status = 'published'
              AND fe.status = 'published'
            ORDER BY fe.display_order, fe.code, q.created_at, q.id
            """
        )
    ).mappings()
    candidates: list[PosttestQuestionCandidate] = []
    for row in rows:
        question_type = str(row["question_type"])
        options = row.get("options") if isinstance(row.get("options"), list) else []
        if question_type == "single_choice" and len(options) < 2:
            continue
        candidates.append(
            PosttestQuestionCandidate(
                id=str(row["id"]),
                experiment_id=str(row["experiment_id"]),
                experiment_title=str(row.get("experiment_title") or row["experiment_id"]),
                question_type=question_type,
                stem=str(row["stem"]),
                options=options,
                answer=row.get("answer") if isinstance(row.get("answer"), dict) else {},
                explanation=str(row["explanation"]) if row.get("explanation") else None,
                difficulty=str(row.get("difficulty") or "basic"),
                related_chapter_ids=[str(item) for item in _as_list(row.get("related_chapter_ids")) if str(item).strip()],
                related_knowledge_point_ids=[
                    str(item) for item in _as_list(row.get("related_knowledge_point_ids")) if str(item).strip()
                ],
                primary_point_node_ids=[str(item) for item in _as_list(row.get("primary_point_node_ids")) if str(item).strip()],
                primary_canonical_point_ids=[str(item) for item in _as_list(row.get("primary_canonical_point_ids")) if str(item).strip()],
                source_placement_node_ids=[str(item) for item in _as_list(row.get("source_placement_node_ids")) if str(item).strip()],
            )
        )
    return _point_backed_candidates(session, candidates)


def _unique(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _all_candidate_point_ids(candidates: list[PosttestQuestionCandidate]) -> list[str]:
    return _unique([point_id for question in candidates for point_id in _question_assessment_point_ids(question)])


def _load_point_info(
    session: Any,
    point_ids: list[str],
    *,
    fallback_experiment_by_point: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    point_ids = _unique(point_ids)
    if not point_ids:
        return {}
    rows = session.execute(
        text(
            """
            WITH RECURSIVE path AS (
              SELECT
                n.id AS point_node_id,
                n.id,
                n.parent_id,
                n.node_kind,
                n.title,
                n.chapter_id,
                n.canonical_point_id,
                0 AS depth
              FROM experiment_catalog_nodes n
              WHERE n.id = ANY(:point_ids)
                AND n.node_kind = 'point'
                AND n.status = 'published'
              UNION ALL
              SELECT
                path.point_node_id,
                parent.id,
                parent.parent_id,
                parent.node_kind,
                parent.title,
                parent.chapter_id,
                parent.canonical_point_id,
                path.depth + 1
              FROM experiment_catalog_nodes parent
              JOIN path ON path.parent_id = parent.id
            ),
            point_rows AS (
              SELECT DISTINCT ON (point_node_id)
                point_node_id,
                id,
                title,
                chapter_id,
                canonical_point_id
              FROM path
              WHERE depth = 0
              ORDER BY point_node_id
            ),
            root_rows AS (
              SELECT DISTINCT ON (point_node_id)
                point_node_id,
                id AS root_node_id,
                title AS root_title,
                chapter_id AS root_chapter_id
              FROM path
              WHERE parent_id IS NULL
              ORDER BY point_node_id, depth DESC
            )
            SELECT
              p.point_node_id,
              p.title AS point_title,
              p.canonical_point_id,
              r.root_node_id,
              r.root_title,
              r.root_chapter_id,
              fe.id AS experiment_id,
              fe.title AS experiment_title
            FROM point_rows p
            JOIN root_rows r ON r.point_node_id = p.point_node_id
            LEFT JOIN formal_experiments fe
              ON fe.metadata->>'catalog_root_node_id' = r.root_node_id
             AND fe.status = 'published'
            ORDER BY r.root_title, p.title, p.point_node_id
            """
        ),
        {"point_ids": point_ids},
    ).mappings()
    fallback = fallback_experiment_by_point or {}
    info: dict[str, dict[str, Any]] = {}
    for row in rows:
        point_node_id = str(row["point_node_id"])
        experiment_id = str(row.get("experiment_id") or "") or fallback.get(point_node_id)
        info[point_node_id] = {
            "id": point_node_id,
            "title": str(row.get("point_title") or point_node_id),
            "canonical_point_id": str(row.get("canonical_point_id") or "") or None,
            "root_node_id": str(row.get("root_node_id") or "") or None,
            "root_title": str(row.get("root_title") or "") or None,
            "experiment_id": experiment_id,
            "experiment_title": str(row.get("experiment_title") or row.get("root_title") or experiment_id or ""),
        }
    return info


def _point_backed_candidates(session: Any, candidates: list[PosttestQuestionCandidate]) -> list[PosttestQuestionCandidate]:
    fallback_experiment_by_point: dict[str, str] = {}
    for question in candidates:
        for point_id in _question_assessment_point_ids(question):
            fallback_experiment_by_point.setdefault(point_id, question.experiment_id)
    point_info = _load_point_info(session, list(fallback_experiment_by_point), fallback_experiment_by_point=fallback_experiment_by_point)
    filtered: list[PosttestQuestionCandidate] = []
    for question in candidates:
        valid_sources = [point_id for point_id in _question_assessment_point_ids(question) if point_id in point_info]
        if not valid_sources:
            continue
        valid_primary = [point_id for point_id in _question_point_node_ids(question) if point_id in point_info] or valid_sources
        canonical_ids = _unique(
            [
                point_info[point_id].get("canonical_point_id")
                for point_id in valid_sources
                if point_info[point_id].get("canonical_point_id")
            ]
        )
        filtered.append(
            replace(
                question,
                primary_point_node_ids=valid_primary,
                source_placement_node_ids=valid_sources,
                primary_canonical_point_ids=canonical_ids,
            )
        )
    return filtered


def _custom_options_from_candidates(
    session: Any,
    candidates: list[PosttestQuestionCandidate],
) -> list[CustomAssessmentExperimentOption]:
    counts: dict[str, int] = {}
    for question in candidates:
        counts[question.experiment_id] = counts.get(question.experiment_id, 0) + 1
    experiment_ids = sorted(counts)
    if not experiment_ids:
        return []
    rows = session.execute(
        text(
            """
            SELECT id, code, title, metadata, display_order
            FROM formal_experiments
            WHERE id = ANY(:experiment_ids)
              AND status = 'published'
            ORDER BY display_order, code
            """
        ),
        {"experiment_ids": experiment_ids},
    ).mappings()
    options: list[CustomAssessmentExperimentOption] = []
    for row in rows:
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        question_count = counts.get(str(row["id"]), 0)
        if question_count <= 0:
            continue
        options.append(
            CustomAssessmentExperimentOption(
                id=str(row["id"]),
                code=str(row.get("code") or ""),
                title=str(row.get("title") or row["id"]),
                parent_code=str(metadata.get("parent_code")) if metadata.get("parent_code") else None,
                parent_title=str(metadata.get("parent_title")) if metadata.get("parent_title") else None,
                question_count=question_count,
            )
        )
    return options


def _ordered_experiment_ids(candidates: list[PosttestQuestionCandidate]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for question in candidates:
        if question.experiment_id in seen:
            continue
        seen.add(question.experiment_id)
        ordered.append(question.experiment_id)
    return ordered


def _load_mastery_map(session: Any, *, student_id: str, point_ids: list[str]) -> dict[str, dict[str, Any]]:
    point_ids = _unique(point_ids)
    if not point_ids:
        return {}
    ensure_student_point_mastery_table(session)
    rows = session.execute(
        text(
            """
            SELECT point_node_id, mastery_score, evidence_count
            FROM student_point_mastery
            WHERE student_id = :student_id
              AND point_node_id = ANY(:point_ids)
            """
        ),
        {"student_id": student_id, "point_ids": point_ids},
    ).mappings()
    return {
        str(row["point_node_id"]): {
            "mastery_score": float(row["mastery_score"]),
            "evidence_count": int(row["evidence_count"] or 0),
        }
        for row in rows
    }


def _draw_tickets(strategy: SmartAssessmentSettings, mastery_score: float) -> float:
    weakness = max(0.0, min(1.0, (100.0 - mastery_score) / 100.0))
    weak_bias = strategy.weak_tendency_percent / 100.0
    tickets = 1.0 + weak_bias * strategy.weak_max_bonus * (weakness ** strategy.weak_curve)
    return round(tickets, 4)


def _weighted_experiment_order(
    experiment_ids: list[str],
    *,
    tickets: dict[str, float],
    seed: str,
) -> list[str]:
    def key(experiment_id: str) -> tuple[float, str]:
        weight = max(float(tickets.get(experiment_id) or 1.0), 0.0001)
        unit = ((_stable_hash(f"{seed}:{experiment_id}") % 10_000_000) + 1) / 10_000_001
        return (-math.log(unit) / weight, experiment_id)

    return sorted(experiment_ids, key=key)


def _stable_experiment_order(experiment_ids: list[str], seed: str) -> list[str]:
    return sorted(experiment_ids, key=lambda experiment_id: (_stable_hash(f"{seed}:{experiment_id}"), experiment_id))


def _ordered_question_pools(
    candidates: list[PosttestQuestionCandidate],
    *,
    student_id: str,
    seed_namespace: str = "smart-assessment",
) -> dict[str, list[PosttestQuestionCandidate]]:
    pools: dict[str, list[PosttestQuestionCandidate]] = defaultdict(list)
    for question in candidates:
        pools[question.experiment_id].append(question)
    return {
        experiment_id: sorted(
            pool,
            key=lambda question: (_stable_hash(f"{student_id}:{seed_namespace}:{experiment_id}:{question.id}"), question.id),
        )
        for experiment_id, pool in pools.items()
    }


def _ordered_point_pools(
    candidates: list[PosttestQuestionCandidate],
    *,
    student_id: str,
    seed_namespace: str = "smart-assessment",
) -> dict[str, list[PosttestQuestionCandidate]]:
    pools: dict[str, list[PosttestQuestionCandidate]] = defaultdict(list)
    for question in candidates:
        for point_id in _question_assessment_point_ids(question):
            pools[point_id].append(question)
    return {
        point_id: sorted(
            pool,
            key=lambda question: (_stable_hash(f"{student_id}:{seed_namespace}:{point_id}:{question.id}"), question.id),
        )
        for point_id, pool in pools.items()
    }


def _point_experiment_map(candidates: list[PosttestQuestionCandidate]) -> dict[str, str]:
    result: dict[str, str] = {}
    for question in candidates:
        for point_id in _question_assessment_point_ids(question):
            result.setdefault(point_id, question.experiment_id)
    return result


def _take_point_questions(
    *,
    order: list[str],
    pools: dict[str, list[PosttestQuestionCandidate]],
    quota: int,
    max_per_experiment: int,
    point_to_experiment: dict[str, str],
    used_questions: set[str],
    used_points: set[str],
    counts: dict[str, int],
    selected: list[PosttestQuestionCandidate],
    source: str,
    point_meta: dict[str, dict[str, Any]],
    question_sources: dict[str, str],
) -> int:
    target = max(0, quota)
    taken = 0
    while taken < target:
        progressed = False
        for point_id in order:
            if taken >= target:
                break
            if point_id in used_points:
                continue
            experiment_id = point_to_experiment.get(point_id)
            if not experiment_id:
                continue
            if counts.get(experiment_id, 0) >= max_per_experiment:
                continue
            pool = pools.get(point_id, [])
            while pool and (pool[0].id in used_questions or not _question_assessment_point_ids(pool[0])):
                pool.pop(0)
            if not pool:
                continue
            question = pool.pop(0)
            selected.append(question)
            used_questions.add(question.id)
            used_points.update(_question_assessment_point_ids(question))
            counts[experiment_id] = counts.get(experiment_id, 0) + 1
            meta = point_meta.setdefault(point_id, {"source": source, "question_count": 0})
            meta["source"] = source
            meta["question_count"] = int(meta.get("question_count") or 0) + 1
            question_sources[question.id] = source
            taken += 1
            progressed = True
        if not progressed:
            break
    return taken


def _take_questions(
    *,
    order: list[str],
    pools: dict[str, list[PosttestQuestionCandidate]],
    quota: int,
    max_per_experiment: int,
    used: set[str],
    counts: dict[str, int],
    selected: list[PosttestQuestionCandidate],
    source: str,
    experiment_meta: dict[str, dict[str, Any]],
) -> int:
    target = max(0, quota)
    taken = 0
    while taken < target:
        progressed = False
        for experiment_id in order:
            if taken >= target:
                break
            if counts.get(experiment_id, 0) >= max_per_experiment:
                continue
            pool = pools.get(experiment_id, [])
            while pool and pool[0].id in used:
                pool.pop(0)
            if not pool:
                continue
            question = pool.pop(0)
            selected.append(question)
            used.add(question.id)
            counts[experiment_id] = counts.get(experiment_id, 0) + 1
            meta = experiment_meta.setdefault(experiment_id, {"source": "measured", "question_count": 0})
            effective_source = str(meta.get("source") or "measured") if source == "any" else source
            meta["source"] = effective_source
            meta["question_count"] = int(meta.get("question_count") or 0) + 1
            taken += 1
            progressed = True
        if not progressed:
            break
    return taken


def _compose_questions(
    *,
    candidates: list[PosttestQuestionCandidate],
    mastery: dict[str, dict[str, Any]],
    strategy: SmartAssessmentSettings,
    student_id: str,
) -> tuple[list[PosttestQuestionCandidate], SmartAssessmentCompositionSummary, dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    point_to_experiment = _point_experiment_map(candidates)
    point_ids = [point_id for point_id in _all_candidate_point_ids(candidates) if point_id in point_to_experiment]
    pools = _ordered_point_pools(candidates, student_id=student_id)
    untested_ids: list[str] = []
    measured_ids: list[str] = []
    tickets: dict[str, float] = {}

    for point_id in point_ids:
        state = mastery.get(point_id)
        evidence_count = int(state.get("evidence_count") or 0) if state else 0
        if evidence_count <= 0:
            untested_ids.append(point_id)
            continue
        measured_ids.append(point_id)
        tickets[point_id] = _draw_tickets(strategy, float(state.get("mastery_score") or 0))

    target_count = strategy.question_count
    untested_target = min(target_count, int(round(target_count * strategy.untested_ratio_percent / 100)))
    measured_target = target_count - untested_target
    untested_order = _stable_experiment_order(untested_ids, f"{student_id}:smart-assessment:untested")
    measured_order = _weighted_experiment_order(measured_ids, tickets=tickets, seed=f"{student_id}:smart-assessment:measured")

    used_questions: set[str] = set()
    used_points: set[str] = set()
    counts: dict[str, int] = {}
    selected: list[PosttestQuestionCandidate] = []
    question_sources: dict[str, str] = {}
    point_meta: dict[str, dict[str, Any]] = {
        point_id: {
            "source": "measured",
            "draw_tickets": tickets[point_id],
            "question_count": 0,
            "reason": "掌握度越低，本轮抽中权重越高",
        }
        for point_id in measured_ids
    }
    for point_id in untested_ids:
        point_meta[point_id] = {
            "source": "untested",
            "draw_tickets": None,
            "question_count": 0,
            "reason": "未测点位按老师设置的比例纳入",
        }

    untested_taken = _take_point_questions(
        order=untested_order,
        pools=pools,
        quota=untested_target,
        max_per_experiment=strategy.max_questions_per_experiment,
        point_to_experiment=point_to_experiment,
        used_questions=used_questions,
        used_points=used_points,
        counts=counts,
        selected=selected,
        source="untested",
        point_meta=point_meta,
        question_sources=question_sources,
    )
    measured_taken = _take_point_questions(
        order=measured_order,
        pools=pools,
        quota=measured_target,
        max_per_experiment=strategy.max_questions_per_experiment,
        point_to_experiment=point_to_experiment,
        used_questions=used_questions,
        used_points=used_points,
        counts=counts,
        selected=selected,
        source="measured",
        point_meta=point_meta,
        question_sources=question_sources,
    )

    if len(selected) < target_count and measured_taken < measured_target:
        untested_taken += _take_point_questions(
            order=untested_order,
            pools=pools,
            quota=target_count - len(selected),
            max_per_experiment=strategy.max_questions_per_experiment,
            point_to_experiment=point_to_experiment,
            used_questions=used_questions,
            used_points=used_points,
            counts=counts,
            selected=selected,
            source="untested",
            point_meta=point_meta,
            question_sources=question_sources,
        )
    if len(selected) < target_count and untested_taken < untested_target:
        measured_taken += _take_point_questions(
            order=measured_order,
            pools=pools,
            quota=target_count - len(selected),
            max_per_experiment=strategy.max_questions_per_experiment,
            point_to_experiment=point_to_experiment,
            used_questions=used_questions,
            used_points=used_points,
            counts=counts,
            selected=selected,
            source="measured",
            point_meta=point_meta,
            question_sources=question_sources,
        )
    if len(selected) < target_count:
        any_order = _stable_experiment_order(point_ids, f"{student_id}:smart-assessment:any")
        _take_point_questions(
            order=any_order,
            pools=pools,
            quota=target_count - len(selected),
            max_per_experiment=strategy.max_questions_per_experiment,
            point_to_experiment=point_to_experiment,
            used_questions=used_questions,
            used_points=used_points,
            counts=counts,
            selected=selected,
            source="measured",
            point_meta=point_meta,
            question_sources=question_sources,
        )

    experiment_meta: dict[str, dict[str, Any]] = {}
    for question in selected:
        source = question_sources.get(question.id, "measured")
        meta = experiment_meta.setdefault(
            question.experiment_id,
            {
                "source": source,
                "draw_tickets": None,
                "question_count": 0,
                "reason": "按点位掌握情况组卷后汇总到实验",
            },
        )
        if meta.get("source") == "untested" and source == "measured":
            meta["source"] = "measured"
        meta["question_count"] = int(meta.get("question_count") or 0) + 1
    selected_point_count = len({point_id for question in selected for point_id in _question_assessment_point_ids(question)})
    untested_count = sum(1 for question in selected if question_sources.get(question.id) == "untested")
    measured_count = len(selected) - untested_count
    composition = SmartAssessmentCompositionSummary(
        total_questions=len(selected),
        target_question_count=target_count,
        selected_point_count=selected_point_count,
        candidate_point_count=len(point_ids),
        untested_question_count=untested_count,
        measured_question_count=measured_count,
        untested_ratio_percent=strategy.untested_ratio_percent,
        weak_tendency_percent=strategy.weak_tendency_percent,
        max_questions_per_experiment=strategy.max_questions_per_experiment,
        warnings={
            "underfilled": len(selected) < target_count,
            "untested_pool_empty": bool(untested_target and not untested_ids),
            "measured_pool_empty": bool(measured_target and not measured_ids),
        },
    )
    return selected, composition, experiment_meta, {
        point_id: {**meta, "question_count": int(meta.get("question_count") or 0)}
        for point_id, meta in point_meta.items()
        if point_id in used_points
    }


def _compose_custom_questions(
    *,
    candidates: list[PosttestQuestionCandidate],
    selected_experiment_ids: list[str],
    settings: CustomAssessmentSettings,
    student_id: str,
    requested_question_count: int,
) -> tuple[list[PosttestQuestionCandidate], SmartAssessmentCompositionSummary, dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    selected_set = set(selected_experiment_ids)
    filtered = [question for question in candidates if question.experiment_id in selected_set]
    point_to_experiment = _point_experiment_map(filtered)
    pools = _ordered_point_pools(filtered, student_id=student_id, seed_namespace="custom-assessment")
    points_by_experiment: dict[str, list[str]] = defaultdict(list)
    for point_id, experiment_id in point_to_experiment.items():
        if experiment_id in selected_set and point_id not in points_by_experiment[experiment_id]:
            points_by_experiment[experiment_id].append(point_id)
    for experiment_id, point_ids in list(points_by_experiment.items()):
        points_by_experiment[experiment_id] = _stable_experiment_order(point_ids, f"{student_id}:custom-assessment:{experiment_id}")
    order = [experiment_id for experiment_id in selected_experiment_ids if points_by_experiment.get(experiment_id)]
    used_questions: set[str] = set()
    used_points: set[str] = set()
    counts: dict[str, int] = {}
    selected: list[PosttestQuestionCandidate] = []
    question_sources: dict[str, str] = {}
    point_meta: dict[str, dict[str, Any]] = {}
    experiment_meta: dict[str, dict[str, Any]] = {
        experiment_id: {
            "source": "custom",
            "draw_tickets": None,
            "question_count": 0,
            "reason": "学生自主选择本轮要练习的实验",
        }
        for experiment_id in order
    }
    target_count = min(requested_question_count, settings.max_question_count)
    quota_by_experiment: dict[str, int] = {}
    if order:
        base = target_count // len(order)
        remainder = target_count % len(order)
        for index, experiment_id in enumerate(order):
            quota_by_experiment[experiment_id] = base + (1 if index < remainder else 0)
    for experiment_id in order:
        _take_point_questions(
            order=points_by_experiment.get(experiment_id, []),
            pools=pools,
            quota=quota_by_experiment.get(experiment_id, 0),
            max_per_experiment=settings.max_questions_per_experiment,
            point_to_experiment=point_to_experiment,
            used_questions=used_questions,
            used_points=used_points,
            counts=counts,
            selected=selected,
            source="custom",
            point_meta=point_meta,
            question_sources=question_sources,
        )
    if len(selected) < target_count:
        all_points = [point_id for experiment_id in order for point_id in points_by_experiment.get(experiment_id, [])]
        _take_point_questions(
            order=all_points,
            pools=pools,
            quota=target_count - len(selected),
            max_per_experiment=settings.max_questions_per_experiment,
            point_to_experiment=point_to_experiment,
            used_questions=used_questions,
            used_points=used_points,
            counts=counts,
            selected=selected,
            source="custom",
            point_meta=point_meta,
            question_sources=question_sources,
        )
    for question in selected:
        meta = experiment_meta.setdefault(
            question.experiment_id,
            {"source": "custom", "draw_tickets": None, "question_count": 0, "reason": "学生自主选择本轮要练习的实验"},
        )
        meta["question_count"] = int(meta.get("question_count") or 0) + 1
    selected_experiments = {question.experiment_id for question in selected}
    experiment_meta = {experiment_id: meta for experiment_id, meta in experiment_meta.items() if experiment_id in selected_experiments}
    composition = SmartAssessmentCompositionSummary(
        total_questions=len(selected),
        target_question_count=target_count,
        requested_question_count=requested_question_count,
        selected_point_count=len({point_id for question in selected for point_id in _question_assessment_point_ids(question)}),
        candidate_point_count=len(point_to_experiment),
        custom_question_count=len(selected),
        max_questions_per_experiment=settings.max_questions_per_experiment,
        warnings={
            "underfilled": len(selected) < target_count,
            "selected_experiment_count": len(selected_experiment_ids),
        },
    )
    return selected, composition, experiment_meta, {
        point_id: {**meta, "question_count": int(meta.get("question_count") or 0)}
        for point_id, meta in point_meta.items()
        if point_id in used_points
    }


def _compose_point_questions(
    *,
    candidates: list[PosttestQuestionCandidate],
    point_node_id: str,
    student_id: str,
    target_question_count: int = POINT_ASSESSMENT_TARGET_COUNT,
) -> tuple[list[PosttestQuestionCandidate], SmartAssessmentCompositionSummary, dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    target = max(1, min(5, int(target_question_count or POINT_ASSESSMENT_TARGET_COUNT)))
    filtered = [question for question in candidates if point_node_id in _question_assessment_point_ids(question)]
    ordered = sorted(
        filtered,
        key=lambda question: (_stable_hash(f"{student_id}:point-assessment:{point_node_id}:{question.id}"), question.id),
    )
    selected = ordered[:target]
    experiment_meta: dict[str, dict[str, Any]] = {}
    for question in selected:
        meta = experiment_meta.setdefault(
            question.experiment_id,
            {
                "source": "point",
                "draw_tickets": None,
                "question_count": 0,
                "reason": "学生完成点位学习后针对当前点位测评",
            },
        )
        meta["question_count"] = int(meta.get("question_count") or 0) + 1
    point_meta = {
        point_node_id: {
            "source": "point",
            "draw_tickets": None,
            "question_count": len(selected),
            "reason": "学生完成点位学习后针对当前点位测评",
        }
    }
    composition = SmartAssessmentCompositionSummary(
        total_questions=len(selected),
        target_question_count=target,
        requested_question_count=target,
        selected_point_count=1 if selected else 0,
        candidate_point_count=1 if filtered else 0,
        custom_question_count=0,
        max_questions_per_experiment=target,
        warnings={
            "underfilled": len(selected) < target,
            "point_question_bank_underfilled": 0 < len(selected) < target,
            "point_node_id": point_node_id,
            "candidate_question_count": len(filtered),
        },
    )
    return selected, composition, experiment_meta, point_meta


def _composition_from_row(row: dict[str, Any], strategy: SmartAssessmentSettings) -> SmartAssessmentCompositionSummary:
    value = row.get("composition_summary")
    if isinstance(value, dict) and value:
        return SmartAssessmentCompositionSummary(**value)
    question_ids = _session_question_ids(row)
    return SmartAssessmentCompositionSummary(
        total_questions=len(question_ids),
        target_question_count=strategy.question_count,
        untested_ratio_percent=strategy.untested_ratio_percent,
        weak_tendency_percent=strategy.weak_tendency_percent,
        max_questions_per_experiment=strategy.max_questions_per_experiment,
    )


def _point_mastery_snapshot(
    session: Any,
    *,
    student_id: str,
    point_ids: list[str],
) -> dict[str, dict[str, Any]]:
    point_ids = _unique(point_ids)
    if not point_ids:
        return {}
    ensure_student_point_mastery_table(session)
    point_info = _load_point_info(session, point_ids)
    current = {
        str(row["point_node_id"]): {
            "mastery_score": float(row["mastery_score"]),
            "mastery_prob": float(row["mastery_prob"]),
            "evidence_count": int(row["evidence_count"] or 0),
        }
        for row in session.execute(
            text(
                """
                SELECT point_node_id, mastery_prob, mastery_score, evidence_count
                FROM student_point_mastery
                WHERE student_id = :student_id
                  AND point_node_id = ANY(:point_ids)
                """
            ),
            {"student_id": student_id, "point_ids": point_ids},
        ).mappings()
    }
    snapshot: dict[str, dict[str, Any]] = {}
    for point_id in point_ids:
        info = point_info.get(point_id)
        if not info:
            continue
        state = current.get(point_id)
        evidence_count = int(state.get("evidence_count") or 0) if state else 0
        snapshot[point_id] = {
            "knowledge_point_id": point_id,
            "point_node_id": point_id,
            "canonical_point_id": info.get("canonical_point_id"),
            "experiment_id": info.get("experiment_id"),
            "experiment_title": info.get("experiment_title"),
            "content": info.get("title") or point_id,
            "mastery_score": float(state["mastery_score"]) if state and evidence_count > 0 else None,
            "mastery_prob": float(state["mastery_prob"]) if state and evidence_count > 0 else None,
            "evidence_count": evidence_count,
        }
    return snapshot


def _point_mastery_changes(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for point_id in sorted(set(before) | set(after)):
        before_item = before.get(point_id) if isinstance(before.get(point_id), dict) else {}
        after_item = after.get(point_id) if isinstance(after.get(point_id), dict) else {}
        before_score = before_item.get("mastery_score")
        after_score = after_item.get("mastery_score")
        before_value = float(before_score) if before_score is not None else 0.0
        after_value = float(after_score) if after_score is not None else 0.0
        content = after_item.get("content") or before_item.get("content") or point_id
        experiment_id = str(after_item.get("experiment_id") or before_item.get("experiment_id") or "")
        changes.append(
            {
                "knowledge_point_id": point_id,
                "point_node_id": point_id,
                "point_title": content,
                "canonical_point_id": after_item.get("canonical_point_id") or before_item.get("canonical_point_id"),
                "experiment_id": experiment_id or None,
                "experiment_title": after_item.get("experiment_title") or before_item.get("experiment_title"),
                "content": content,
                "before_score": round(before_value, 2),
                "after_score": round(after_value, 2),
                "delta": round(after_value - before_value, 2),
            }
        )
    return sorted(changes, key=lambda item: (item["after_score"], item["knowledge_point_id"]))


def _experiment_total_point_counts(session: Any, experiment_ids: list[str]) -> dict[str, int]:
    if not experiment_ids:
        return {}
    rows = session.execute(
        text(
            """
            SELECT q.experiment_id, COUNT(DISTINCT p.point_node_id) AS point_count
            FROM experiment_questions q
            JOIN LATERAL (
              SELECT unnest(
                CASE
                  WHEN array_length(q.source_placement_node_ids, 1) > 0 THEN q.source_placement_node_ids
                  ELSE q.primary_point_node_ids
                END
              ) AS point_node_id
            ) p ON true
            JOIN experiment_catalog_nodes n ON n.id = p.point_node_id
            WHERE q.status = 'published'
              AND q.experiment_id = ANY(:experiment_ids)
              AND n.node_kind = 'point'
              AND n.status = 'published'
            GROUP BY q.experiment_id
            """
        ),
        {"experiment_ids": experiment_ids},
    ).mappings()
    return {str(row["experiment_id"]): int(row["point_count"] or 0) for row in rows}


def _experiments_for_session(
    session: Any,
    *,
    experiment_ids: list[str],
    point_ids: list[str],
    mastery_before: dict[str, Any],
    metadata: dict[str, Any],
) -> list[SmartAssessmentExperimentSummary]:
    summaries = _load_experiment_summaries(session, experiment_ids)
    meta = metadata.get("experiment_sources") if isinstance(metadata.get("experiment_sources"), dict) else {}
    point_source_meta = metadata.get("point_sources") if isinstance(metadata.get("point_sources"), dict) else {}
    total_point_counts = _experiment_total_point_counts(session, experiment_ids)
    point_info = _load_point_info(session, point_ids)
    points_by_experiment: dict[str, list[SmartAssessmentPointSummary]] = defaultdict(list)
    for point_id in point_ids:
        info = point_info.get(point_id)
        if not info:
            continue
        mastery = mastery_before.get(point_id) if isinstance(mastery_before.get(point_id), dict) else {}
        source_meta = point_source_meta.get(point_id) if isinstance(point_source_meta.get(point_id), dict) else {}
        source = str(source_meta.get("source") or ("measured" if int(mastery.get("evidence_count") or 0) > 0 else "untested"))
        if source not in ASSESSMENT_SOURCE_VALUES:
            source = "untested"
        experiment_id = str(info.get("experiment_id") or "")
        points_by_experiment[experiment_id].append(
            SmartAssessmentPointSummary(
                id=point_id,
                title=str(info.get("title") or point_id),
                experiment_id=experiment_id or None,
                experiment_title=str(info.get("experiment_title") or "") or None,
                canonical_point_id=str(info.get("canonical_point_id") or "") or None,
                mastery_score=float(mastery.get("mastery_score")) if mastery.get("mastery_score") is not None else None,
                before_score=float(mastery.get("mastery_score")) if mastery.get("mastery_score") is not None else None,
                evidence_count=int(mastery.get("evidence_count") or 0),
                source=source,  # type: ignore[arg-type]
                draw_tickets=float(source_meta.get("draw_tickets")) if source_meta.get("draw_tickets") is not None else None,
                question_count=int(source_meta.get("question_count") or 0),
                reason=str(source_meta.get("reason")) if source_meta.get("reason") else None,
            )
        )
    results: list[SmartAssessmentExperimentSummary] = []
    for summary in summaries:
        source_meta = meta.get(summary.id) if isinstance(meta.get(summary.id), dict) else {}
        points = sorted(points_by_experiment.get(summary.id, []), key=lambda point: (point.source != "untested", point.mastery_score or 101, point.title))
        measured_scores = [float(point.mastery_score) for point in points if point.mastery_score is not None and point.evidence_count > 0]
        evidence_count = sum(point.evidence_count for point in points)
        source = str(source_meta.get("source") or ("measured" if measured_scores else "untested"))
        if source not in ASSESSMENT_SOURCE_VALUES:
            source = "untested"
        results.append(
            SmartAssessmentExperimentSummary(
                id=summary.id,
                code=summary.code,
                title=summary.title,
                parent_code=summary.parent_code,
                parent_title=summary.parent_title,
                mastery_score=round(sum(measured_scores) / len(measured_scores), 2) if measured_scores else None,
                evidence_count=evidence_count,
                source=source,  # type: ignore[arg-type]
                draw_tickets=float(source_meta.get("draw_tickets")) if source_meta.get("draw_tickets") is not None else None,
                question_count=int(source_meta.get("question_count") or 0),
                measured_point_count=sum(1 for point in points if point.evidence_count > 0),
                total_point_count=max(total_point_counts.get(summary.id, 0), len(points)),
                weak_point_count=sum(1 for point in points if point.mastery_score is not None and point.mastery_score < 60),
                reason=str(source_meta.get("reason")) if source_meta.get("reason") else None,
                points=points,
            )
        )
    return results


def _response_for_session(session: Any, row: dict[str, Any]) -> StudentSmartAssessmentResponse:
    question_ids = _session_question_ids(row)
    questions = _load_questions_by_ids(session, question_ids)
    ordered_questions = [questions[question_id] for question_id in question_ids if question_id in questions]
    strategy = _strategy_from_value(row.get("strategy_snapshot") if isinstance(row.get("strategy_snapshot"), dict) else {})
    mastery_before = row.get("mastery_before") if isinstance(row.get("mastery_before"), dict) else {}
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    point_ids = _session_point_node_ids(row) or _unique(
        [point_id for question in ordered_questions for point_id in _question_assessment_point_ids(question)]
    )
    return StudentSmartAssessmentResponse(
        status="in_progress",
        session_id=str(row["id"]),
        assessment_mode=_assessment_mode_from_value(row.get("assessment_mode")),  # type: ignore[arg-type]
        strategy=strategy,
        composition=_composition_from_row(row, strategy),
        experiments=_experiments_for_session(
            session,
            experiment_ids=_session_experiment_ids(row),
            point_ids=point_ids,
            mastery_before=mastery_before,
            metadata=metadata,
        ),
        questions=[_public_question(question) for question in ordered_questions],
    )


def _custom_strategy_snapshot(settings: CustomAssessmentSettings, question_count: int) -> SmartAssessmentSettings:
    return SmartAssessmentSettings(
        enabled=settings.enabled,
        question_count=question_count,
        untested_ratio_percent=0,
        weak_tendency_percent=0,
        max_questions_per_experiment=settings.max_questions_per_experiment,
        weak_curve=2.0,
        weak_max_bonus=9.0,
    )


def get_student_assessment_status(user: Any) -> StudentAssessmentStatusResponse:
    with db_session() as session:
        _ensure_tables(session)
        context = _load_student_context(session, user)
        _ensure_student_row(session, context)
        open_session = _load_open_session(session, context.student_id)
        completed_smart_baseline = bool(
            session.execute(
                text(
                    """
                    SELECT 1
                    FROM student_smart_assessment_sessions
                    WHERE student_id = :student_id
                      AND status = 'completed'
                      AND assessment_mode = 'smart'
                    LIMIT 1
                    """
                ),
                {"student_id": context.student_id},
            ).scalar_one_or_none()
        )
        baseline_prompt_dismissed = bool(
            session.execute(
                text(
                    """
                    SELECT 1
                    FROM student_events
                    WHERE student_id = :student_id
                      AND event_type = :event_type
                    LIMIT 1
                    """
                ),
                {"student_id": context.student_id, "event_type": SMART_BASELINE_PROMPT_DISMISSED_EVENT},
            ).scalar_one_or_none()
        )
        return StudentAssessmentStatusResponse(
            has_completed_smart_baseline=completed_smart_baseline,
            has_open_assessment=bool(open_session),
            open_session_id=str(open_session["id"]) if open_session else None,
            open_assessment_mode=_assessment_mode_from_value(open_session.get("assessment_mode")) if open_session else None,  # type: ignore[arg-type]
            smart_baseline_prompt_dismissed=baseline_prompt_dismissed,
        )


def dismiss_student_smart_baseline_prompt(user: Any) -> StudentAssessmentStatusResponse:
    with db_session() as session:
        _ensure_tables(session)
        context = _load_student_context(session, user)
        _ensure_student_row(session, context)
        already_dismissed = bool(
            session.execute(
                text(
                    """
                    SELECT 1
                    FROM student_events
                    WHERE student_id = :student_id
                      AND event_type = :event_type
                    LIMIT 1
                    """
                ),
                {"student_id": context.student_id, "event_type": SMART_BASELINE_PROMPT_DISMISSED_EVENT},
            ).scalar_one_or_none()
        )
        if not already_dismissed:
            session.execute(
                text(
                    """
                    INSERT INTO student_events (student_id, event_type, difficulty, metadata, created_at)
                    VALUES (:student_id, :event_type, 'basic', CAST(:metadata AS jsonb), now())
                    """
                ),
                {
                    "student_id": context.student_id,
                    "event_type": SMART_BASELINE_PROMPT_DISMISSED_EVENT,
                    "metadata": _json({"source": "student_h5_assessment_prompt"}),
                },
            )
        open_session = _load_open_session(session, context.student_id)
        completed_smart_baseline = bool(
            session.execute(
                text(
                    """
                    SELECT 1
                    FROM student_smart_assessment_sessions
                    WHERE student_id = :student_id
                      AND status = 'completed'
                      AND assessment_mode = 'smart'
                    LIMIT 1
                    """
                ),
                {"student_id": context.student_id},
            ).scalar_one_or_none()
        )
        return StudentAssessmentStatusResponse(
            has_completed_smart_baseline=completed_smart_baseline,
            has_open_assessment=bool(open_session),
            open_session_id=str(open_session["id"]) if open_session else None,
            open_assessment_mode=_assessment_mode_from_value(open_session.get("assessment_mode")) if open_session else None,  # type: ignore[arg-type]
            smart_baseline_prompt_dismissed=True,
        )


def start_student_smart_assessment(user: Any) -> StudentSmartAssessmentResponse:
    with db_session() as session:
        _ensure_tables(session)
        context = _load_student_context(session, user)
        _ensure_student_row(session, context)
        strategy, _inherited, _has_override = _effective_strategy(session, context.class_id)
        if not strategy.enabled:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Smart assessment is disabled")

        existing = _load_open_session(session, context.student_id)
        if existing:
            return _response_for_session(session, existing)

        candidates = _load_all_published_candidates(session)
        if not candidates:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Smart assessment question bank is not configured")

        candidate_experiment_ids = _ordered_experiment_ids(candidates)
        candidate_point_ids = _all_candidate_point_ids(candidates)
        mastery_map = _load_mastery_map(session, student_id=context.student_id, point_ids=candidate_point_ids)
        selected, composition, experiment_meta, point_meta = _compose_questions(
            candidates=candidates,
            mastery=mastery_map,
            strategy=strategy,
            student_id=context.student_id,
        )
        if not selected:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Smart assessment question bank is not configured")

        experiment_ids = []
        seen: set[str] = set()
        for question in selected:
            if question.experiment_id in seen:
                continue
            seen.add(question.experiment_id)
            experiment_ids.append(question.experiment_id)
        point_node_ids = _unique([point_id for question in selected for point_id in _question_assessment_point_ids(question)])
        canonical_point_ids = _unique([point_id for question in selected for point_id in _question_assessment_canonical_ids(question)])
        mastery_before = _point_mastery_snapshot(session, student_id=context.student_id, point_ids=point_node_ids)
        metadata = {
            "experiment_sources": experiment_meta,
            "point_sources": point_meta,
            "candidate_experiment_count": len(candidate_experiment_ids),
            "candidate_point_count": len(candidate_point_ids),
        }

        row = (
            session.execute(
                text(
                    """
                    INSERT INTO student_smart_assessment_sessions (
                      student_id, class_id, status, assessment_mode, strategy_snapshot, composition_summary,
                      experiment_ids, point_node_ids, canonical_point_ids, source_placement_node_ids,
                      question_ids, mastery_before, metadata
                    )
                    VALUES (
                      :student_id, :class_id, 'in_progress', 'smart',
                      CAST(:strategy_snapshot AS jsonb), CAST(:composition_summary AS jsonb),
                      CAST(:experiment_ids AS jsonb), CAST(:point_node_ids AS jsonb),
                      CAST(:canonical_point_ids AS jsonb), CAST(:source_placement_node_ids AS jsonb),
                      CAST(:question_ids AS jsonb),
                      CAST(:mastery_before AS jsonb), CAST(:metadata AS jsonb)
                    )
                    RETURNING *
                    """
                ),
                {
                    "student_id": context.student_id,
                    "class_id": context.class_id,
                    "strategy_snapshot": _json(_model_dump(strategy)),
                    "composition_summary": _json(_model_dump(composition)),
                    "experiment_ids": _json_array(experiment_ids),
                    "point_node_ids": _json_array(point_node_ids),
                    "canonical_point_ids": _json_array(canonical_point_ids),
                    "source_placement_node_ids": _json_array(point_node_ids),
                    "question_ids": _json_array(_question_ids(selected)),
                    "mastery_before": _json(mastery_before),
                    "metadata": _json(metadata),
                },
            )
            .mappings()
            .one()
        )
        session.execute(
            text(
                """
                INSERT INTO student_events (student_id, event_type, difficulty, metadata, created_at)
                VALUES (:student_id, 'smart_assessment_started', 'basic', CAST(:metadata AS jsonb), now())
                """
            ),
            {
                "student_id": context.student_id,
                "metadata": _json(
                    {
                        "smart_assessment_session_id": str(row["id"]),
                        "experiment_ids": experiment_ids,
                        "point_node_ids": point_node_ids,
                        "question_count": len(selected),
                        "strategy": _model_dump(strategy),
                    }
                ),
            },
        )
        return _response_for_session(session, dict(row))


def get_student_custom_assessment_options(user: Any) -> StudentCustomAssessmentOptionsResponse:
    with db_session() as session:
        _ensure_tables(session)
        context = _load_student_context(session, user)
        settings, _inherited, _has_override = _effective_custom_settings(session, context.class_id)
        candidates = _load_all_published_candidates(session) if settings.enabled else []
        return StudentCustomAssessmentOptionsResponse(
            settings=_custom_options_settings(settings),
            experiments=_custom_options_from_candidates(session, candidates),
        )


def start_student_custom_assessment(
    user: Any,
    payload: StudentCustomAssessmentStartRequest,
) -> StudentSmartAssessmentResponse:
    requested_experiment_ids: list[str] = []
    seen_requested: set[str] = set()
    for experiment_id in payload.experiment_ids:
        experiment_id = str(experiment_id).strip()
        if experiment_id and experiment_id not in seen_requested:
            requested_experiment_ids.append(experiment_id)
            seen_requested.add(experiment_id)
    if not requested_experiment_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select at least one experiment")

    with db_session() as session:
        _ensure_tables(session)
        context = _load_student_context(session, user)
        _ensure_student_row(session, context)
        settings, _inherited, _has_override = _effective_custom_settings(session, context.class_id)
        if not settings.enabled:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Custom assessment is disabled")

        existing = _load_open_session(session, context.student_id)
        if existing:
            return _response_for_session(session, existing)

        options_settings = _custom_options_settings(settings)
        if payload.question_count not in options_settings.question_count_options:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question count is not allowed")

        candidates = _load_all_published_candidates(session)
        options = _custom_options_from_candidates(session, candidates)
        allowed_ids = {option.id for option in options}
        invalid_ids = [experiment_id for experiment_id in requested_experiment_ids if experiment_id not in allowed_ids]
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Selected experiments are not available for custom assessment", "experiment_ids": invalid_ids},
            )
        if not candidates or not options:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Custom assessment question bank is not configured")

        selected, composition, experiment_meta, point_meta = _compose_custom_questions(
            candidates=candidates,
            selected_experiment_ids=requested_experiment_ids,
            settings=settings,
            student_id=context.student_id,
            requested_question_count=payload.question_count,
        )
        if not selected:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected experiments do not have available questions")

        experiment_ids = []
        seen: set[str] = set()
        for question in selected:
            if question.experiment_id in seen:
                continue
            seen.add(question.experiment_id)
            experiment_ids.append(question.experiment_id)
        point_node_ids = _unique([point_id for question in selected for point_id in _question_assessment_point_ids(question)])
        canonical_point_ids = _unique([point_id for question in selected for point_id in _question_assessment_canonical_ids(question)])
        mastery_before = _point_mastery_snapshot(session, student_id=context.student_id, point_ids=point_node_ids)
        strategy = _custom_strategy_snapshot(settings, composition.target_question_count)
        metadata = {
            "assessment_mode": "custom",
            "experiment_sources": experiment_meta,
            "point_sources": point_meta,
            "candidate_experiment_count": len(options),
            "candidate_point_count": len(_all_candidate_point_ids(candidates)),
            "requested_experiment_ids": requested_experiment_ids,
            "selected_experiment_count": len(experiment_ids),
            "custom_assessment_settings": _model_dump(settings),
        }

        row = (
            session.execute(
                text(
                    """
                    INSERT INTO student_smart_assessment_sessions (
                      student_id, class_id, status, assessment_mode, strategy_snapshot, composition_summary,
                      experiment_ids, point_node_ids, canonical_point_ids, source_placement_node_ids,
                      question_ids, mastery_before, metadata
                    )
                    VALUES (
                      :student_id, :class_id, 'in_progress', 'custom',
                      CAST(:strategy_snapshot AS jsonb), CAST(:composition_summary AS jsonb),
                      CAST(:experiment_ids AS jsonb), CAST(:point_node_ids AS jsonb),
                      CAST(:canonical_point_ids AS jsonb), CAST(:source_placement_node_ids AS jsonb),
                      CAST(:question_ids AS jsonb),
                      CAST(:mastery_before AS jsonb), CAST(:metadata AS jsonb)
                    )
                    RETURNING *
                    """
                ),
                {
                    "student_id": context.student_id,
                    "class_id": context.class_id,
                    "strategy_snapshot": _json(_model_dump(strategy)),
                    "composition_summary": _json(_model_dump(composition)),
                    "experiment_ids": _json_array(experiment_ids),
                    "point_node_ids": _json_array(point_node_ids),
                    "canonical_point_ids": _json_array(canonical_point_ids),
                    "source_placement_node_ids": _json_array(point_node_ids),
                    "question_ids": _json_array(_question_ids(selected)),
                    "mastery_before": _json(mastery_before),
                    "metadata": _json(metadata),
                },
            )
            .mappings()
            .one()
        )
        session.execute(
            text(
                """
                INSERT INTO student_events (student_id, event_type, difficulty, metadata, created_at)
                VALUES (:student_id, 'custom_assessment_started', 'basic', CAST(:metadata AS jsonb), now())
                """
            ),
            {
                "student_id": context.student_id,
                "metadata": _json(
                    {
                        "smart_assessment_session_id": str(row["id"]),
                        "assessment_mode": "custom",
                        "experiment_ids": experiment_ids,
                        "point_node_ids": point_node_ids,
                        "question_count": len(selected),
                        "requested_question_count": payload.question_count,
                    }
                ),
            },
        )
        return _response_for_session(session, dict(row))


def start_student_point_assessment(
    user: Any,
    payload: StudentPointAssessmentStartRequest,
) -> StudentSmartAssessmentResponse:
    point_node_id = str(payload.point_node_id).strip()
    if not point_node_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Point node id is required")

    with db_session() as session:
        _ensure_tables(session)
        context = _load_student_context(session, user)
        _ensure_student_row(session, context)

        existing = _load_open_session(session, context.student_id)
        if existing:
            return _response_for_session(session, existing)

        candidates = _load_all_published_candidates(session)
        if not candidates:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Point assessment question bank is not configured")

        selected, composition, experiment_meta, point_meta = _compose_point_questions(
            candidates=candidates,
            point_node_id=point_node_id,
            student_id=context.student_id,
        )
        if not selected:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This point does not have available assessment questions")

        experiment_ids = []
        seen: set[str] = set()
        for question in selected:
            if question.experiment_id in seen:
                continue
            seen.add(question.experiment_id)
            experiment_ids.append(question.experiment_id)
        point_node_ids = _unique([point_node_id])
        canonical_point_ids = _unique([point_id for question in selected for point_id in _question_assessment_canonical_ids(question)])
        mastery_before = _point_mastery_snapshot(session, student_id=context.student_id, point_ids=point_node_ids)
        strategy = SmartAssessmentSettings(
            enabled=True,
            question_count=composition.target_question_count,
            untested_ratio_percent=0,
            weak_tendency_percent=0,
            max_questions_per_experiment=composition.target_question_count,
            weak_curve=2.0,
            weak_max_bonus=9.0,
        )
        metadata = {
            "assessment_mode": "point",
            "experiment_sources": experiment_meta,
            "point_sources": point_meta,
            "requested_point_node_id": point_node_id,
            "candidate_question_count": composition.warnings.get("candidate_question_count"),
        }

        row = (
            session.execute(
                text(
                    """
                    INSERT INTO student_smart_assessment_sessions (
                      student_id, class_id, status, assessment_mode, strategy_snapshot, composition_summary,
                      experiment_ids, point_node_ids, canonical_point_ids, source_placement_node_ids,
                      question_ids, mastery_before, metadata
                    )
                    VALUES (
                      :student_id, :class_id, 'in_progress', 'point',
                      CAST(:strategy_snapshot AS jsonb), CAST(:composition_summary AS jsonb),
                      CAST(:experiment_ids AS jsonb), CAST(:point_node_ids AS jsonb),
                      CAST(:canonical_point_ids AS jsonb), CAST(:source_placement_node_ids AS jsonb),
                      CAST(:question_ids AS jsonb),
                      CAST(:mastery_before AS jsonb), CAST(:metadata AS jsonb)
                    )
                    RETURNING *
                    """
                ),
                {
                    "student_id": context.student_id,
                    "class_id": context.class_id,
                    "strategy_snapshot": _json(_model_dump(strategy)),
                    "composition_summary": _json(_model_dump(composition)),
                    "experiment_ids": _json_array(experiment_ids),
                    "point_node_ids": _json_array(point_node_ids),
                    "canonical_point_ids": _json_array(canonical_point_ids),
                    "source_placement_node_ids": _json_array(point_node_ids),
                    "question_ids": _json_array(_question_ids(selected)),
                    "mastery_before": _json(mastery_before),
                    "metadata": _json(metadata),
                },
            )
            .mappings()
            .one()
        )
        session.execute(
            text(
                """
                INSERT INTO student_events (student_id, event_type, difficulty, metadata, created_at)
                VALUES (:student_id, 'point_assessment_started', 'basic', CAST(:metadata AS jsonb), now())
                """
            ),
            {
                "student_id": context.student_id,
                "metadata": _json(
                    {
                        "smart_assessment_session_id": str(row["id"]),
                        "assessment_mode": "point",
                        "point_node_id": point_node_id,
                        "experiment_ids": experiment_ids,
                        "question_count": len(selected),
                    }
                ),
            },
        )
        return _response_for_session(session, dict(row))


def _validate_submitted_answers(question_ids: list[str], payload: StudentSmartAssessmentSubmitRequest) -> dict[str, Any]:
    expected = set(question_ids)
    submitted = {answer.question_id for answer in payload.answers}
    if len(payload.answers) != len(submitted) or submitted != expected:
        missing = sorted(expected - submitted)
        extra = sorted(submitted - expected)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Submitted answers must match the assessment questions", "missing": missing, "extra": extra},
        )
    return {answer.question_id: answer.answer for answer in payload.answers}


def _insert_attempts(
    session: Any,
    *,
    student_id: str,
    class_id: str | None,
    smart_assessment_session_id: str,
    assessment_mode: str,
    questions: list[PosttestQuestionCandidate],
    answers: dict[str, Any],
) -> list[dict[str, Any]]:
    graded: list[dict[str, Any]] = []
    attempt_kind = _attempt_kind_for_assessment_mode(assessment_mode)
    for question in questions:
        submitted = answers[question.id]
        correct = _grade_answer(question.question_type, question.answer, submitted)
        graded.append({"question": question, "correct": correct, "submitted": submitted})
        session.execute(
            text(
                """
                INSERT INTO experiment_question_attempts (
                  student_id, class_id, experiment_id, question_id, question_type,
                  point_node_id, canonical_point_id, source_placement_node_id,
                  submitted_answer, correct, score, attempt_kind, metadata
                )
                VALUES (
                  :student_id, :class_id, :experiment_id, CAST(:question_id AS uuid), :question_type,
                  :point_node_id, :canonical_point_id, :source_placement_node_id,
                  CAST(:submitted_answer AS jsonb), :correct, :score, :attempt_kind, CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "student_id": student_id,
                "class_id": class_id,
                "experiment_id": question.experiment_id,
                "question_id": question.id,
                "question_type": question.question_type,
                "point_node_id": next(iter(_question_assessment_point_ids(question)), None),
                "canonical_point_id": next(iter(_question_assessment_canonical_ids(question)), None),
                "source_placement_node_id": next(iter(_question_assessment_point_ids(question)), None),
                "submitted_answer": _json({"value": submitted}),
                "correct": correct,
                "score": 1 if correct else 0,
                "attempt_kind": attempt_kind,
                "metadata": _json(
                    {
                        "smart_assessment_session_id": smart_assessment_session_id,
                        "assessment_mode": assessment_mode,
                        "point_node_ids": _question_point_node_ids(question),
                        "source_placement_node_ids": _question_assessment_point_ids(question),
                        "canonical_point_ids": _question_assessment_canonical_ids(question),
                        "related_chapter_ids": question.related_chapter_ids,
                        "related_knowledge_point_ids": question.related_knowledge_point_ids,
                    }
                ),
            },
        )
    return graded


def _update_mastery_from_smart_assessment(session: Any, *, student_id: str, smart_assessment_session_id: str) -> None:
    attempt_rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT a.correct, a.class_id, a.experiment_id, a.point_node_id,
                       a.canonical_point_id, a.source_placement_node_id, a.question_type,
                       q.difficulty, q.related_knowledge_point_ids,
                       q.primary_point_node_ids, q.primary_canonical_point_ids, q.source_placement_node_ids,
                       a.metadata
                FROM experiment_question_attempts a
                JOIN experiment_questions q ON q.id = a.question_id
                WHERE a.student_id = :student_id
                  AND a.metadata->>'smart_assessment_session_id' = :smart_assessment_session_id
                ORDER BY a.created_at, a.id
                """
            ),
            {"student_id": student_id, "smart_assessment_session_id": smart_assessment_session_id},
        )
        .mappings()
        .all()
    ]
    assessment_mode = "smart"
    mode_value = session.execute(
        text("SELECT assessment_mode FROM student_smart_assessment_sessions WHERE id = CAST(:id AS uuid)"),
        {"id": smart_assessment_session_id},
    ).scalar_one_or_none()
    assessment_mode = _assessment_mode_from_value(mode_value)
    for row in attempt_rows:
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        row["point_node_ids"] = _as_list(metadata.get("point_node_ids")) or _as_list(row.get("primary_point_node_ids"))
        row["source_placement_node_ids"] = (
            _as_list(metadata.get("source_placement_node_ids"))
            or _as_list(row.get("source_placement_node_ids"))
            or _as_list(row.get("point_node_id"))
        )
        row["canonical_point_ids"] = _as_list(metadata.get("canonical_point_ids")) or _as_list(row.get("primary_canonical_point_ids"))
    update_point_mastery_from_attempt_rows(
        session,
        student_id=student_id,
        class_id=next((str(row.get("class_id")) for row in attempt_rows if row.get("class_id")), None),
        attempt_rows=attempt_rows,
        evidence_kind=_attempt_kind_for_assessment_mode(assessment_mode),
        evidence_id=smart_assessment_session_id,
    )
    kp_ids = sorted(
        {
            str(kp_id)
            for row in attempt_rows
            for kp_id in _as_list(row.get("related_knowledge_point_ids"))
            if str(kp_id).strip()
        }
    )
    if not kp_ids:
        return
    valid_kp_ids = {
        str(row["id"])
        for row in session.execute(text("SELECT id FROM knowledge_points WHERE id = ANY(:kp_ids)"), {"kp_ids": kp_ids}).mappings()
    }
    current = {
        str(row["knowledge_point_id"]): [float(value) for value in row["state_prob"]]
        for row in session.execute(
            text(
                """
                SELECT knowledge_point_id, state_prob
                FROM student_mastery
                WHERE student_id = :student_id
                  AND knowledge_point_id = ANY(:kp_ids)
                """
            ),
            {"student_id": student_id, "kp_ids": list(valid_kp_ids)},
        ).mappings()
    }
    next_states: dict[str, dict[str, Any]] = {}
    for row in attempt_rows:
        correct = bool(row.get("correct"))
        event_type = "answer_correct" if correct else "answer_wrong"
        for kp_id in _as_list(row.get("related_knowledge_point_ids")):
            kp_id = str(kp_id)
            if kp_id not in valid_kp_ids:
                continue
            state = next_states.get(kp_id, {"state_prob": current.get(kp_id)})
            next_states[kp_id] = update_mastery(
                state.get("state_prob"),
                event_type,
                str(row.get("difficulty") or "basic"),
                correct,
            )
    for kp_id, state in next_states.items():
        session.execute(
            text(
                """
                INSERT INTO student_mastery (
                  student_id, knowledge_point_id, state_prob, mastery_score, updated_at
                )
                VALUES (:student_id, :kp_id, :state_prob, :mastery_score, now())
                ON CONFLICT (student_id, knowledge_point_id)
                DO UPDATE SET
                  state_prob = EXCLUDED.state_prob,
                  mastery_score = EXCLUDED.mastery_score,
                  updated_at = now()
                """
            ),
            {
                "student_id": student_id,
                "kp_id": kp_id,
                "state_prob": state["state_prob"],
                "mastery_score": state["mastery_score"],
            },
        )


def _update_experiment_progress(
    session: Any,
    *,
    student_id: str,
    class_id: str | None,
    experiment_ids: list[str],
    score: float,
    correct_count: int,
    total_count: int,
    assessment_mode: str = "smart",
) -> None:
    attempt_kind = _attempt_kind_for_assessment_mode(assessment_mode)
    status_value = "completed" if total_count and score >= 60 else ("needs_attention" if total_count else "in_progress")
    for experiment_id in experiment_ids:
        session.execute(
            text(
                """
                INSERT INTO student_experiment_progress (
                  student_id, class_id, experiment_id, status, completion_percent,
                  best_score, last_activity_at, completed_at, metadata, updated_at
                )
                VALUES (
                  :student_id, :class_id, :experiment_id, :status, 100,
                  :score, now(), CASE WHEN :status = 'completed' THEN now() ELSE NULL END,
                  CAST(:metadata AS jsonb), now()
                )
                ON CONFLICT (student_id, experiment_id) DO UPDATE SET
                  class_id = EXCLUDED.class_id,
                  status = EXCLUDED.status,
                  completion_percent = GREATEST(student_experiment_progress.completion_percent, EXCLUDED.completion_percent),
                  best_score = GREATEST(COALESCE(student_experiment_progress.best_score, 0), COALESCE(EXCLUDED.best_score, 0)),
                  last_activity_at = now(),
                  completed_at = COALESCE(student_experiment_progress.completed_at, EXCLUDED.completed_at),
                  metadata = EXCLUDED.metadata,
                  updated_at = now()
                """
            ),
            {
                "student_id": student_id,
                "class_id": class_id,
                "experiment_id": experiment_id,
                "status": status_value,
                "score": score,
                "metadata": _json(
                    {
                        "attempt_kind": attempt_kind,
                        "assessment_mode": assessment_mode,
                        "correct_count": correct_count,
                        "total_count": total_count,
                        "score": score,
                    }
                ),
            },
        )


def _build_report(
    *,
    row: dict[str, Any],
    experiments: list[SmartAssessmentExperimentSummary],
    questions: list[PosttestQuestionCandidate],
    graded: list[dict[str, Any]],
    mastery_after: dict[str, Any],
) -> StudentSmartAssessmentReport:
    session_id = str(row["id"])
    correct_count = sum(1 for item in graded if item["correct"])
    total_count = len(graded)
    score = round(100 * correct_count / total_count, 2) if total_count else 0.0
    before = row.get("mastery_before") if isinstance(row.get("mastery_before"), dict) else {}
    before_avg = _mastery_average(before)
    after_avg = _mastery_average(mastery_after)
    changes = _point_mastery_changes(before, mastery_after)
    question_map = {question.id: question for question in questions}
    wrong_answers = [
        StudentSmartAssessmentWrongAnswer(
            question_id=question.id,
            experiment_id=question.experiment_id,
            experiment_title=question.experiment_title,
            point_node_ids=_question_assessment_point_ids(question),
            canonical_point_ids=_question_assessment_canonical_ids(question),
            question_type=question.question_type,
            stem=question.stem,
            options=question.options,
            submitted_answer=item["submitted"],
            correct_answer=_answer_key(question),
            explanation=question.explanation,
        )
        for item in graded
        for question in [question_map[str(item["question"].id)]]
        if not item["correct"]
    ]
    recommendation = "本轮智能测评已全部答对，可以继续挑战更薄弱的点位。"
    assessment_mode = _assessment_mode_from_value(row.get("assessment_mode"))
    if assessment_mode == "custom":
        recommendation = "本轮自主测评已完成，可以根据错题回顾继续复习相关实验。"
    if assessment_mode == "point":
        recommendation = "本轮点位测评已完成，可以回到刚学习的点位继续复盘。"
    if wrong_answers:
        recommendation = "优先复习错题对应的实验点位；系统会在下一轮继续提高薄弱点位的抽中权重。"
        if assessment_mode == "custom":
            recommendation = "优先复习本次自选实验中的错题，再按需要重新选择实验练习。"
        if assessment_mode == "point":
            recommendation = "优先复习刚学习点位中的错题，再回到点位视频和原理说明查漏补缺。"
    strategy = _strategy_from_value(row.get("strategy_snapshot") if isinstance(row.get("strategy_snapshot"), dict) else {})
    return StudentSmartAssessmentReport(
        session_id=session_id,
        assessment_mode=assessment_mode,
        strategy=strategy,
        composition=_composition_from_row(row, strategy),
        experiments=experiments,
        correct_count=correct_count,
        total_count=total_count,
        score=score,
        correct_rate=round(correct_count / total_count, 4) if total_count else 0,
        mastery_before_average=before_avg,
        mastery_after_average=after_avg,
        mastery_delta=round(after_avg - before_avg, 2) if before_avg is not None and after_avg is not None else None,
        mastery_changes=changes,
        wrong_answers=wrong_answers,
        next_recommendation=recommendation,
    )


def submit_student_smart_assessment(user: Any, payload: StudentSmartAssessmentSubmitRequest) -> StudentSmartAssessmentSubmitResponse:
    with db_session() as session:
        _ensure_tables(session)
        context = _load_student_context(session, user)
        _ensure_student_row(session, context)
        current = _load_open_session(session, context.student_id)
        if not current or str(current["id"]) != payload.session_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active assessment session")
        assessment_mode = _assessment_mode_from_value(current.get("assessment_mode"))

        question_ids = _session_question_ids(current)
        answers = _validate_submitted_answers(question_ids, payload)
        questions_by_id = _load_questions_by_ids(session, question_ids)
        if len(questions_by_id) != len(question_ids):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Smart assessment question bank has changed")
        ordered_questions = [questions_by_id[question_id] for question_id in question_ids]

        session_id = str(current["id"])
        graded = _insert_attempts(
            session,
            student_id=context.student_id,
            class_id=context.class_id,
            smart_assessment_session_id=session_id,
            assessment_mode=assessment_mode,
            questions=ordered_questions,
            answers=answers,
        )
        correct_count = sum(1 for item in graded if item["correct"])
        total_count = len(graded)
        score = round(100 * correct_count / total_count, 2) if total_count else 0.0
        experiment_ids = _session_experiment_ids(current)
        point_ids = _session_point_node_ids(current) or _unique(
            [point_id for question in ordered_questions for point_id in _question_assessment_point_ids(question)]
        )
        metadata = current.get("metadata") if isinstance(current.get("metadata"), dict) else {}
        experiments = _experiments_for_session(
            session,
            experiment_ids=experiment_ids,
            point_ids=point_ids,
            mastery_before=current.get("mastery_before") if isinstance(current.get("mastery_before"), dict) else {},
            metadata=metadata,
        )
        _update_mastery_from_smart_assessment(session, student_id=context.student_id, smart_assessment_session_id=session_id)
        mastery_after = _point_mastery_snapshot(session, student_id=context.student_id, point_ids=point_ids)
        _update_experiment_progress(
            session,
            student_id=context.student_id,
            class_id=context.class_id,
            experiment_ids=experiment_ids,
            score=score,
            correct_count=correct_count,
            total_count=total_count,
            assessment_mode=assessment_mode,
        )
        session.execute(
            text(
                """
                INSERT INTO student_events (
                  student_id, event_type, difficulty, correct, metadata, created_at
                )
                VALUES (
                  :student_id, :event_type, 'basic', :correct, CAST(:metadata AS jsonb), now()
                )
                """
            ),
            {
                "student_id": context.student_id,
                "event_type": _assessment_submit_event_type(assessment_mode),
                "correct": score >= 60 if total_count else None,
                "metadata": _json(
                    {
                        "smart_assessment_session_id": session_id,
                        "assessment_mode": assessment_mode,
                        "experiment_ids": experiment_ids,
                        "score": score,
                        "correct_count": correct_count,
                        "total_count": total_count,
                    }
                ),
            },
        )
        updated = (
            session.execute(
                text(
                    """
                    UPDATE student_smart_assessment_sessions
                    SET status = 'completed',
                        score = :score,
                        correct_count = :correct_count,
                        total_count = :total_count,
                        mastery_after = CAST(:mastery_after AS jsonb),
                        completed_at = now(),
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    RETURNING *
                    """
                ),
                {
                    "id": session_id,
                    "score": score,
                    "correct_count": correct_count,
                    "total_count": total_count,
                    "mastery_after": _json(mastery_after),
                },
            )
            .mappings()
            .one()
        )
        report = _build_report(
            row=dict(updated),
            experiments=experiments,
            questions=ordered_questions,
            graded=graded,
            mastery_after=mastery_after,
        )
        session.execute(
            text(
                """
                UPDATE student_smart_assessment_sessions
                SET report = CAST(:report AS jsonb)
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {"id": session_id, "report": json.dumps(_model_dump(report), ensure_ascii=False, default=str)},
        )
        return StudentSmartAssessmentSubmitResponse(status="completed", report=report)
