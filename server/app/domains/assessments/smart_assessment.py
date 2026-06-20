from __future__ import annotations

import json
import math
from collections import defaultdict
from typing import Any

from sqlalchemy import text

from server.app.domains.assessments.mastery import update_experiment_mastery_from_attempt_rows
from server.app.domains.assessments.posttest import (
    PosttestQuestionCandidate,
    _answer_key,
    _as_list,
    _experiment_mastery_snapshot,
    _experiment_summary_from_row,
    _json,
    _json_array,
    _load_experiment_summaries,
    _load_questions_by_ids,
    _mastery_average,
    _mastery_changes,
    _question_ids,
    _session_experiment_ids,
    _session_question_ids,
    _stable_hash,
)
from server.app.domains.assessments.pretest import _ensure_student_row, _load_student_context
from server.app.domains.assessments.student_experiment import _grade_answer
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.domains.platform.settings import SmartAssessmentSettings, get_learning_behavior_settings
from server.app.domains.roster.classes import require_class_access
from server.app.infrastructure.database import db_session
from server.app.mastery import update_mastery
from server.app.student_smart_assessment_schemas import (
    PublicSmartAssessmentQuestion,
    SmartAssessmentCompositionSummary,
    SmartAssessmentExperimentSummary,
    SmartAssessmentStrategyResponse,
    StudentSmartAssessmentReport,
    StudentSmartAssessmentResponse,
    StudentSmartAssessmentSubmitRequest,
    StudentSmartAssessmentSubmitResponse,
    StudentSmartAssessmentWrongAnswer,
)


_CREATE_SMART_ASSESSMENT_SQL = """
CREATE TABLE IF NOT EXISTS student_smart_assessment_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id text NOT NULL,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  status text NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),
  strategy_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
  composition_summary jsonb NOT NULL DEFAULT '{}'::jsonb,
  experiment_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
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

CREATE TABLE IF NOT EXISTS class_smart_assessment_settings (
  class_id text PRIMARY KEY REFERENCES classes(id) ON DELETE CASCADE,
  value jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
"""


def _ensure_tables(session: Any) -> None:
    session.connection().exec_driver_sql(_CREATE_SMART_ASSESSMENT_SQL)


def _model_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _strategy_from_value(value: Any, fallback: SmartAssessmentSettings | None = None) -> SmartAssessmentSettings:
    base = _model_dump(fallback or SmartAssessmentSettings())
    if isinstance(value, dict):
        base.update(value)
    return SmartAssessmentSettings(**base)


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


def _public_question(question: PosttestQuestionCandidate) -> PublicSmartAssessmentQuestion:
    return PublicSmartAssessmentQuestion(
        id=question.id,
        experiment_id=question.experiment_id,
        experiment_title=question.experiment_title,
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
                   q.difficulty, q.related_chapter_ids, q.related_knowledge_point_ids
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
            )
        )
    return candidates


def _ordered_experiment_ids(candidates: list[PosttestQuestionCandidate]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for question in candidates:
        if question.experiment_id in seen:
            continue
        seen.add(question.experiment_id)
        ordered.append(question.experiment_id)
    return ordered


def _load_mastery_map(session: Any, *, student_id: str, experiment_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not experiment_ids:
        return {}
    rows = session.execute(
        text(
            """
            SELECT experiment_id, mastery_score, evidence_count
            FROM student_experiment_mastery
            WHERE student_id = :student_id
              AND experiment_id = ANY(:experiment_ids)
            """
        ),
        {"student_id": student_id, "experiment_ids": experiment_ids},
    ).mappings()
    return {
        str(row["experiment_id"]): {
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
) -> dict[str, list[PosttestQuestionCandidate]]:
    pools: dict[str, list[PosttestQuestionCandidate]] = defaultdict(list)
    for question in candidates:
        pools[question.experiment_id].append(question)
    return {
        experiment_id: sorted(
            pool,
            key=lambda question: (_stable_hash(f"{student_id}:smart-assessment:{experiment_id}:{question.id}"), question.id),
        )
        for experiment_id, pool in pools.items()
    }


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
) -> tuple[list[PosttestQuestionCandidate], SmartAssessmentCompositionSummary, dict[str, dict[str, Any]]]:
    experiment_ids = _ordered_experiment_ids(candidates)
    pools = _ordered_question_pools(candidates, student_id=student_id)
    untested_ids: list[str] = []
    measured_ids: list[str] = []
    tickets: dict[str, float] = {}

    for experiment_id in experiment_ids:
        state = mastery.get(experiment_id)
        evidence_count = int(state.get("evidence_count") or 0) if state else 0
        if evidence_count <= 0:
            untested_ids.append(experiment_id)
            continue
        measured_ids.append(experiment_id)
        tickets[experiment_id] = _draw_tickets(strategy, float(state.get("mastery_score") or 0))

    target_count = strategy.question_count
    untested_target = min(target_count, int(round(target_count * strategy.untested_ratio_percent / 100)))
    measured_target = target_count - untested_target
    untested_order = _stable_experiment_order(untested_ids, f"{student_id}:smart-assessment:untested")
    measured_order = _weighted_experiment_order(measured_ids, tickets=tickets, seed=f"{student_id}:smart-assessment:measured")

    used: set[str] = set()
    counts: dict[str, int] = {}
    selected: list[PosttestQuestionCandidate] = []
    experiment_meta: dict[str, dict[str, Any]] = {
        experiment_id: {
            "source": "measured",
            "draw_tickets": tickets[experiment_id],
            "question_count": 0,
            "reason": "掌握度越低，本轮抽中权重越高",
        }
        for experiment_id in measured_ids
    }
    for experiment_id in untested_ids:
        experiment_meta[experiment_id] = {
            "source": "untested",
            "draw_tickets": None,
            "question_count": 0,
            "reason": "未测实验按老师设置的比例纳入",
        }

    untested_taken = _take_questions(
        order=untested_order,
        pools=pools,
        quota=untested_target,
        max_per_experiment=strategy.max_questions_per_experiment,
        used=used,
        counts=counts,
        selected=selected,
        source="untested",
        experiment_meta=experiment_meta,
    )
    measured_taken = _take_questions(
        order=measured_order,
        pools=pools,
        quota=measured_target,
        max_per_experiment=strategy.max_questions_per_experiment,
        used=used,
        counts=counts,
        selected=selected,
        source="measured",
        experiment_meta=experiment_meta,
    )

    if len(selected) < target_count and measured_taken < measured_target:
        untested_taken += _take_questions(
            order=untested_order,
            pools=pools,
            quota=target_count - len(selected),
            max_per_experiment=strategy.max_questions_per_experiment,
            used=used,
            counts=counts,
            selected=selected,
            source="untested",
            experiment_meta=experiment_meta,
        )
    if len(selected) < target_count and untested_taken < untested_target:
        measured_taken += _take_questions(
            order=measured_order,
            pools=pools,
            quota=target_count - len(selected),
            max_per_experiment=strategy.max_questions_per_experiment,
            used=used,
            counts=counts,
            selected=selected,
            source="any",
            experiment_meta=experiment_meta,
        )
    if len(selected) < target_count:
        any_order = _stable_experiment_order(experiment_ids, f"{student_id}:smart-assessment:any")
        _take_questions(
            order=any_order,
            pools=pools,
            quota=target_count - len(selected),
            max_per_experiment=strategy.max_questions_per_experiment,
            used=used,
            counts=counts,
            selected=selected,
            source="measured",
            experiment_meta=experiment_meta,
        )

    selected_experiment_ids = {question.experiment_id for question in selected}
    experiment_meta = {
        experiment_id: {**meta, "question_count": int(meta.get("question_count") or 0)}
        for experiment_id, meta in experiment_meta.items()
        if experiment_id in selected_experiment_ids
    }
    untested_count = sum(1 for question in selected if experiment_meta.get(question.experiment_id, {}).get("source") == "untested")
    measured_count = len(selected) - untested_count
    composition = SmartAssessmentCompositionSummary(
        total_questions=len(selected),
        target_question_count=target_count,
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
    return selected, composition, experiment_meta


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


def _experiments_for_session(
    session: Any,
    *,
    experiment_ids: list[str],
    mastery_before: dict[str, Any],
    metadata: dict[str, Any],
) -> list[SmartAssessmentExperimentSummary]:
    summaries = _load_experiment_summaries(session, experiment_ids)
    meta = metadata.get("experiment_sources") if isinstance(metadata.get("experiment_sources"), dict) else {}
    results: list[SmartAssessmentExperimentSummary] = []
    for summary in summaries:
        mastery = mastery_before.get(summary.id) if isinstance(mastery_before.get(summary.id), dict) else {}
        source_meta = meta.get(summary.id) if isinstance(meta.get(summary.id), dict) else {}
        source = str(source_meta.get("source") or ("measured" if int(mastery.get("evidence_count") or 0) > 0 else "untested"))
        results.append(
            SmartAssessmentExperimentSummary(
                id=summary.id,
                code=summary.code,
                title=summary.title,
                parent_code=summary.parent_code,
                parent_title=summary.parent_title,
                mastery_score=float(mastery.get("mastery_score")) if mastery.get("mastery_score") is not None else None,
                evidence_count=int(mastery.get("evidence_count") or 0),
                source="measured" if source == "measured" else "untested",
                draw_tickets=float(source_meta.get("draw_tickets")) if source_meta.get("draw_tickets") is not None else None,
                question_count=int(source_meta.get("question_count") or 0),
                reason=str(source_meta.get("reason")) if source_meta.get("reason") else None,
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
    return StudentSmartAssessmentResponse(
        status="in_progress",
        session_id=str(row["id"]),
        strategy=strategy,
        composition=_composition_from_row(row, strategy),
        experiments=_experiments_for_session(
            session,
            experiment_ids=_session_experiment_ids(row),
            mastery_before=mastery_before,
            metadata=metadata,
        ),
        questions=[_public_question(question) for question in ordered_questions],
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
        mastery_map = _load_mastery_map(session, student_id=context.student_id, experiment_ids=candidate_experiment_ids)
        selected, composition, experiment_meta = _compose_questions(
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
        experiments = _load_experiment_summaries(session, experiment_ids)
        mastery_before = _experiment_mastery_snapshot(session, student_id=context.student_id, experiments=experiments)
        metadata = {
            "experiment_sources": experiment_meta,
            "candidate_experiment_count": len(candidate_experiment_ids),
        }

        row = (
            session.execute(
                text(
                    """
                    INSERT INTO student_smart_assessment_sessions (
                      student_id, class_id, status, strategy_snapshot, composition_summary,
                      experiment_ids, question_ids, mastery_before, metadata
                    )
                    VALUES (
                      :student_id, :class_id, 'in_progress',
                      CAST(:strategy_snapshot AS jsonb), CAST(:composition_summary AS jsonb),
                      CAST(:experiment_ids AS jsonb), CAST(:question_ids AS jsonb),
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
                        "question_count": len(selected),
                        "strategy": _model_dump(strategy),
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
            detail={"message": "Submitted answers must match the smart assessment questions", "missing": missing, "extra": extra},
        )
    return {answer.question_id: answer.answer for answer in payload.answers}


def _insert_attempts(
    session: Any,
    *,
    student_id: str,
    class_id: str | None,
    smart_assessment_session_id: str,
    questions: list[PosttestQuestionCandidate],
    answers: dict[str, Any],
) -> list[dict[str, Any]]:
    graded: list[dict[str, Any]] = []
    for question in questions:
        submitted = answers[question.id]
        correct = _grade_answer(question.question_type, question.answer, submitted)
        graded.append({"question": question, "correct": correct, "submitted": submitted})
        session.execute(
            text(
                """
                INSERT INTO experiment_question_attempts (
                  student_id, class_id, experiment_id, question_id, question_type,
                  submitted_answer, correct, score, attempt_kind, metadata
                )
                VALUES (
                  :student_id, :class_id, :experiment_id, CAST(:question_id AS uuid), :question_type,
                  CAST(:submitted_answer AS jsonb), :correct, :score, 'smart_assessment', CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "student_id": student_id,
                "class_id": class_id,
                "experiment_id": question.experiment_id,
                "question_id": question.id,
                "question_type": question.question_type,
                "submitted_answer": _json({"value": submitted}),
                "correct": correct,
                "score": 1 if correct else 0,
                "metadata": _json(
                    {
                        "smart_assessment_session_id": smart_assessment_session_id,
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
                SELECT a.correct, a.class_id, a.experiment_id, a.question_type,
                       q.difficulty, q.related_knowledge_point_ids
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
    update_experiment_mastery_from_attempt_rows(
        session,
        student_id=student_id,
        class_id=next((str(row.get("class_id")) for row in attempt_rows if row.get("class_id")), None),
        attempt_rows=attempt_rows,
        evidence_kind="smart_assessment",
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
) -> None:
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
                        "attempt_kind": "smart_assessment",
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
    changes = _mastery_changes(before, mastery_after)
    question_map = {question.id: question for question in questions}
    wrong_answers = [
        StudentSmartAssessmentWrongAnswer(
            question_id=question.id,
            experiment_id=question.experiment_id,
            experiment_title=question.experiment_title,
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
    recommendation = "本轮智能测评已全部答对，可以继续挑战更薄弱的实验。"
    if wrong_answers:
        recommendation = "优先复习错题对应的实验现象和解释；系统会在下一轮继续提高薄弱实验的抽中权重。"
    strategy = _strategy_from_value(row.get("strategy_snapshot") if isinstance(row.get("strategy_snapshot"), dict) else {})
    return StudentSmartAssessmentReport(
        session_id=session_id,
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
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active smart assessment session")

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
            questions=ordered_questions,
            answers=answers,
        )
        correct_count = sum(1 for item in graded if item["correct"])
        total_count = len(graded)
        score = round(100 * correct_count / total_count, 2) if total_count else 0.0
        experiment_ids = _session_experiment_ids(current)
        metadata = current.get("metadata") if isinstance(current.get("metadata"), dict) else {}
        experiments = _experiments_for_session(
            session,
            experiment_ids=experiment_ids,
            mastery_before=current.get("mastery_before") if isinstance(current.get("mastery_before"), dict) else {},
            metadata=metadata,
        )
        base_experiments = _load_experiment_summaries(session, experiment_ids)
        _update_mastery_from_smart_assessment(session, student_id=context.student_id, smart_assessment_session_id=session_id)
        mastery_after = _experiment_mastery_snapshot(session, student_id=context.student_id, experiments=base_experiments)
        _update_experiment_progress(
            session,
            student_id=context.student_id,
            class_id=context.class_id,
            experiment_ids=experiment_ids,
            score=score,
            correct_count=correct_count,
            total_count=total_count,
        )
        session.execute(
            text(
                """
                INSERT INTO student_events (
                  student_id, event_type, difficulty, correct, metadata, created_at
                )
                VALUES (
                  :student_id, 'smart_assessment_submit', 'basic', :correct, CAST(:metadata AS jsonb), now()
                )
                """
            ),
            {
                "student_id": context.student_id,
                "correct": score >= 60 if total_count else None,
                "metadata": _json(
                    {
                        "smart_assessment_session_id": session_id,
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
