from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from sqlalchemy import text

from server.app.infrastructure.database import db_session
from server.app.mastery import DEFAULT_EXPERIMENT_MASTERY_SCORE, MasterySnapshot, update_mastery
from server.app.domains.platform.settings import get_learning_behavior_settings
from server.app.domains.assessments.mastery import update_experiment_mastery_from_attempt_rows
from server.app.domains.assessments.student_experiment import _grade_answer
from server.app.domains.questions.point_identity import unique_strings
from server.app.domains.assessments.pretest import _ensure_student_row, _load_student_context
from server.app.student_posttest_schemas import (
    PosttestExperimentSummary,
    PublicPosttestQuestion,
    StudentPosttestReport,
    StudentPosttestResponse,
    StudentPosttestSubmitRequest,
    StudentPosttestSubmitResponse,
    StudentPosttestWrongAnswer,
)


@dataclass(frozen=True)
class PosttestQuestionCandidate:
    id: str
    experiment_id: str
    experiment_title: str
    question_type: str
    stem: str
    options: list[Any]
    answer: dict[str, Any]
    explanation: str | None
    difficulty: str
    related_chapter_ids: list[str]
    related_knowledge_point_ids: list[str]
    primary_point_node_ids: list[str] = field(default_factory=list)
    primary_canonical_point_ids: list[str] = field(default_factory=list)
    source_placement_node_ids: list[str] = field(default_factory=list)


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _json_array(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False, default=str)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _question_point_node_ids(question: PosttestQuestionCandidate) -> list[str]:
    return [str(item) for item in question.primary_point_node_ids if str(item).strip()]


def _question_source_placement_node_ids(question: PosttestQuestionCandidate) -> list[str]:
    return unique_strings(question.source_placement_node_ids, question.primary_point_node_ids)


def _question_canonical_point_ids(question: PosttestQuestionCandidate) -> list[str]:
    return unique_strings(question.primary_canonical_point_ids)


def _stable_hash(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)


def _stable_sample(items: list[PosttestQuestionCandidate], count: int, seed: str) -> list[PosttestQuestionCandidate]:
    return sorted(items, key=lambda item: (_stable_hash(f"{seed}:{item.id}"), item.id))[:count]


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata")
    return value if isinstance(value, dict) else {}


def _question_ids(questions: list[PosttestQuestionCandidate]) -> list[str]:
    return [question.id for question in questions]


def _session_question_ids(row: dict[str, Any]) -> list[str]:
    return [str(item) for item in _as_list(row.get("question_ids")) if str(item).strip()]


def _session_experiment_ids(row: dict[str, Any]) -> list[str]:
    return [str(item) for item in _as_list(row.get("experiment_ids")) if str(item).strip()]


def _public_question(question: PosttestQuestionCandidate) -> PublicPosttestQuestion:
    return PublicPosttestQuestion(
        id=question.id,
        experiment_id=question.experiment_id,
        experiment_title=question.experiment_title,
        question_type=question.question_type,  # type: ignore[arg-type]
        stem=question.stem,
        options=question.options,
        related_chapter_ids=question.related_chapter_ids,
        related_knowledge_point_ids=question.related_knowledge_point_ids,
    )


def _load_open_session(session: Any, student_id: str) -> dict[str, Any] | None:
    row = (
        session.execute(
            text(
                """
                SELECT *
                FROM student_posttest_sessions
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


def _latest_completed_at(session: Any, student_id: str) -> Any:
    return session.execute(
        text(
            """
            SELECT completed_at
            FROM student_posttest_sessions
            WHERE student_id = :student_id
              AND status = 'completed'
            ORDER BY completed_at DESC NULLS LAST, created_at DESC
            LIMIT 1
            """
        ),
        {"student_id": student_id},
    ).scalar()


def _experiment_summary_from_row(row: dict[str, Any]) -> PosttestExperimentSummary:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    return PosttestExperimentSummary(
        id=str(row["id"]),
        code=str(row.get("code") or ""),
        title=str(row.get("title") or row["id"]),
        parent_code=str(metadata.get("parent_code")) if metadata.get("parent_code") else None,
        parent_title=str(metadata.get("parent_title")) if metadata.get("parent_title") else None,
    )


def _load_learning_experiments(session: Any, *, student_id: str) -> list[PosttestExperimentSummary]:
    after_at = _latest_completed_at(session, student_id)
    rows = session.execute(
        text(
            """
            WITH opened AS (
              SELECT
                se.metadata->>'experiment_id' AS experiment_id,
                min(se.created_at) AS first_opened_at
              FROM student_events se
              WHERE se.student_id = :student_id
                AND se.event_type = 'experiment_detail_opened'
                AND se.metadata->>'experiment_id' IS NOT NULL
                AND (CAST(:after_at AS timestamptz) IS NULL OR se.created_at > CAST(:after_at AS timestamptz))
              GROUP BY se.metadata->>'experiment_id'
            )
            SELECT fe.id, fe.code, fe.title, fe.metadata, opened.first_opened_at, fe.display_order
            FROM opened
            JOIN formal_experiments fe ON fe.id = opened.experiment_id
            WHERE fe.status = 'published'
            ORDER BY opened.first_opened_at, fe.display_order, fe.code
            """
        ),
        {"student_id": student_id, "after_at": after_at},
    ).mappings()
    return [_experiment_summary_from_row(dict(row)) for row in rows]


def _load_experiment_summaries(session: Any, experiment_ids: list[str]) -> list[PosttestExperimentSummary]:
    if not experiment_ids:
        return []
    rows = session.execute(
        text(
            """
            SELECT id, code, title, metadata, display_order
            FROM formal_experiments
            WHERE id = ANY(:experiment_ids)
              AND status = 'published'
            ORDER BY array_position(:experiment_ids, id), display_order, code
            """
        ),
        {"experiment_ids": experiment_ids},
    ).mappings()
    return [_experiment_summary_from_row(dict(row)) for row in rows]


def _load_questions_by_ids(session: Any, question_ids: list[str]) -> dict[str, PosttestQuestionCandidate]:
    if not question_ids:
        return {}
    rows = session.execute(
        text(
            """
            SELECT q.id::text AS id, q.experiment_id, fe.title AS experiment_title,
                   q.question_type, q.stem, q.options, q.answer, q.explanation,
                   q.difficulty, q.related_chapter_ids, q.related_knowledge_point_ids,
                   q.primary_point_node_ids, q.primary_canonical_point_ids, q.source_placement_node_ids
            FROM experiment_questions q
            JOIN formal_experiments fe ON fe.id = q.experiment_id
            WHERE q.id::text = ANY(:question_ids)
              AND q.status = 'published'
            """
        ),
        {"question_ids": question_ids},
    ).mappings()
    questions: dict[str, PosttestQuestionCandidate] = {}
    for row in rows:
        options = row.get("options") if isinstance(row.get("options"), list) else []
        questions[str(row["id"])] = PosttestQuestionCandidate(
            id=str(row["id"]),
            experiment_id=str(row["experiment_id"]),
            experiment_title=str(row.get("experiment_title") or row["experiment_id"]),
            question_type=str(row["question_type"]),
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
    return questions


def _load_published_candidates(session: Any, experiment_ids: list[str]) -> list[PosttestQuestionCandidate]:
    if not experiment_ids:
        return []
    rows = session.execute(
        text(
            """
            SELECT q.id::text AS id, q.experiment_id, fe.title AS experiment_title,
                   q.question_type, q.stem, q.options, q.answer, q.explanation,
                   q.difficulty, q.related_chapter_ids, q.related_knowledge_point_ids,
                   q.primary_point_node_ids, q.primary_canonical_point_ids, q.source_placement_node_ids
            FROM experiment_questions q
            JOIN formal_experiments fe ON fe.id = q.experiment_id
            WHERE q.experiment_id = ANY(:experiment_ids)
              AND q.status = 'published'
            ORDER BY array_position(:experiment_ids, q.experiment_id), q.created_at, q.id
            """
        ),
        {"experiment_ids": experiment_ids},
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
    return candidates


def _balanced_posttest_sample(
    candidates: list[PosttestQuestionCandidate],
    *,
    experiment_ids: list[str],
    student_id: str,
    count: int,
) -> list[PosttestQuestionCandidate]:
    pools: dict[str, list[PosttestQuestionCandidate]] = defaultdict(list)
    for question in candidates:
        pools[question.experiment_id].append(question)
    ordered_pools = {
        experiment_id: _stable_sample(pools.get(experiment_id, []), len(pools.get(experiment_id, [])), f"{student_id}:posttest:{experiment_id}")
        for experiment_id in experiment_ids
    }
    selected: list[PosttestQuestionCandidate] = []
    used: set[str] = set()
    while len(selected) < count:
        progressed = False
        for experiment_id in experiment_ids:
            pool = ordered_pools.get(experiment_id, [])
            while pool and pool[0].id in used:
                pool.pop(0)
            if not pool:
                continue
            question = pool.pop(0)
            selected.append(question)
            used.add(question.id)
            progressed = True
            if len(selected) >= count:
                break
        if not progressed:
            break
    return selected


def _knowledge_point_ids(questions: list[PosttestQuestionCandidate]) -> list[str]:
    ids: set[str] = set()
    for question in questions:
        ids.update(question.related_knowledge_point_ids)
    return sorted(kp_id for kp_id in ids if kp_id)


def _mastery_snapshot(session: Any, *, student_id: str, kp_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not kp_ids:
        return {}
    knowledge_points = {
        str(row["id"]): str(row.get("content") or "")
        for row in session.execute(
            text("SELECT id, content FROM knowledge_points WHERE id = ANY(:kp_ids)"),
            {"kp_ids": kp_ids},
        ).mappings()
    }
    current = {
        str(row["knowledge_point_id"]): {
            "state_prob": [float(value) for value in row["state_prob"]],
            "mastery_score": float(row["mastery_score"]),
        }
        for row in session.execute(
            text(
                """
                SELECT knowledge_point_id, state_prob, mastery_score
                FROM student_mastery
                WHERE student_id = :student_id
                  AND knowledge_point_id = ANY(:kp_ids)
                """
            ),
            {"student_id": student_id, "kp_ids": list(knowledge_points)},
        ).mappings()
    }
    initial = MasterySnapshot.initial()
    snapshot: dict[str, dict[str, Any]] = {}
    for kp_id in sorted(knowledge_points):
        state = current.get(kp_id)
        snapshot[kp_id] = {
            "content": knowledge_points[kp_id],
            "state_prob": state["state_prob"] if state else initial.state_prob,
            "mastery_score": state["mastery_score"] if state else initial.mastery_score,
        }
    return snapshot


def _experiment_mastery_snapshot(
    session: Any,
    *,
    student_id: str,
    experiments: list[PosttestExperimentSummary],
) -> dict[str, dict[str, Any]]:
    experiment_ids = [experiment.id for experiment in experiments if experiment.id]
    if not experiment_ids:
        return {}
    current = {
        str(row["experiment_id"]): {
            "mastery_score": float(row["mastery_score"]),
            "evidence_count": int(row["evidence_count"] or 0),
        }
        for row in session.execute(
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
    }
    snapshot: dict[str, dict[str, Any]] = {}
    for experiment in experiments:
        state = current.get(experiment.id)
        snapshot[experiment.id] = {
            "experiment_id": experiment.id,
            "content": experiment.title or experiment.code or experiment.id,
            "mastery_score": state["mastery_score"] if state else DEFAULT_EXPERIMENT_MASTERY_SCORE,
            "evidence_count": state["evidence_count"] if state else 0,
        }
    return snapshot


def _response_for_session(session: Any, row: dict[str, Any]) -> StudentPosttestResponse:
    question_ids = _session_question_ids(row)
    questions = _load_questions_by_ids(session, question_ids)
    ordered_questions = [questions[question_id] for question_id in question_ids if question_id in questions]
    return StudentPosttestResponse(
        status="in_progress",
        session_id=str(row["id"]),
        experiments=_load_experiment_summaries(session, _session_experiment_ids(row)),
        questions=[_public_question(question) for question in ordered_questions],
    )


def start_student_posttest(user: Any) -> StudentPosttestResponse:
    settings = get_learning_behavior_settings()
    if not settings.assessment.posttest_enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Posttest is disabled")

    with db_session() as session:
        context = _load_student_context(session, user)
        _ensure_student_row(session, context)
        existing = _load_open_session(session, context.student_id)
        if existing:
            return _response_for_session(session, existing)

        experiments = _load_learning_experiments(session, student_id=context.student_id)
        if not experiments:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No learning experiments to assess")

        experiment_ids = [experiment.id for experiment in experiments]
        candidates = _load_published_candidates(session, experiment_ids)
        if not candidates:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Posttest question bank is not configured")

        target_count = settings.assessment.posttest_question_count
        selected = _balanced_posttest_sample(
            candidates,
            experiment_ids=experiment_ids,
            student_id=context.student_id,
            count=target_count,
        )
        if not selected:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Posttest question bank is not configured")
        mastery_before = _experiment_mastery_snapshot(session, student_id=context.student_id, experiments=experiments)
        metadata = {
            "experiments": [experiment.model_dump() for experiment in experiments],
            "point_node_ids": sorted({node_id for question in selected for node_id in _question_point_node_ids(question)}),
            "source_placement_node_ids": sorted(
                {node_id for question in selected for node_id in _question_source_placement_node_ids(question)}
            ),
            "canonical_point_ids": sorted({node_id for question in selected for node_id in _question_canonical_point_ids(question)}),
            "target_question_count": target_count,
            "warnings": {"underfilled": len(selected) < target_count},
        }
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO student_posttest_sessions (
                      student_id, class_id, status, experiment_ids, question_ids,
                      point_node_ids, canonical_point_ids, source_placement_node_ids, mastery_before, metadata
                    )
                    VALUES (
                      :student_id, :class_id, 'in_progress', CAST(:experiment_ids AS jsonb),
                      CAST(:question_ids AS jsonb), CAST(:point_node_ids AS jsonb),
                      CAST(:canonical_point_ids AS jsonb), CAST(:source_placement_node_ids AS jsonb),
                      CAST(:mastery_before AS jsonb),
                      CAST(:metadata AS jsonb)
                    )
                    RETURNING *
                    """
                ),
                {
                    "student_id": context.student_id,
                    "class_id": context.class_id,
                    "experiment_ids": _json_array(experiment_ids),
                    "question_ids": _json_array(_question_ids(selected)),
                    "point_node_ids": _json_array(metadata["point_node_ids"]),
                    "canonical_point_ids": _json_array(metadata["canonical_point_ids"]),
                    "source_placement_node_ids": _json_array(metadata["source_placement_node_ids"]),
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
                VALUES (:student_id, 'posttest_started', 'basic', CAST(:metadata AS jsonb), now())
                """
            ),
            {
                "student_id": context.student_id,
                "metadata": _json(
                    {
                        "posttest_session_id": str(row["id"]),
                        "experiment_ids": experiment_ids,
                        "question_count": len(selected),
                    }
                ),
            },
        )
        return _response_for_session(session, dict(row))


def _validate_submitted_answers(question_ids: list[str], payload: StudentPosttestSubmitRequest) -> dict[str, Any]:
    expected = set(question_ids)
    submitted = {answer.question_id for answer in payload.answers}
    if len(payload.answers) != len(submitted) or submitted != expected:
        missing = sorted(expected - submitted)
        extra = sorted(submitted - expected)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Submitted answers must match the posttest questions", "missing": missing, "extra": extra},
        )
    return {answer.question_id: answer.answer for answer in payload.answers}


def _insert_attempts(
    session: Any,
    *,
    student_id: str,
    class_id: str | None,
    posttest_session_id: str,
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
                  point_node_id, canonical_point_id, source_placement_node_id,
                  submitted_answer, correct, score, attempt_kind, metadata
                )
                VALUES (
                  :student_id, :class_id, :experiment_id, CAST(:question_id AS uuid), :question_type,
                  :point_node_id, :canonical_point_id, :source_placement_node_id,
                  CAST(:submitted_answer AS jsonb), :correct, :score, 'posttest', CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "student_id": student_id,
                "class_id": class_id,
                "experiment_id": question.experiment_id,
                "question_id": question.id,
                "question_type": question.question_type,
                "point_node_id": next(iter(_question_source_placement_node_ids(question)), None),
                "canonical_point_id": next(iter(_question_canonical_point_ids(question)), None),
                "source_placement_node_id": next(iter(_question_source_placement_node_ids(question)), None),
                "submitted_answer": _json({"value": submitted}),
                "correct": correct,
                "score": 1 if correct else 0,
                "metadata": _json(
                    {
                        "posttest_session_id": posttest_session_id,
                        "point_node_ids": _question_point_node_ids(question),
                        "source_placement_node_ids": _question_source_placement_node_ids(question),
                        "canonical_point_ids": _question_canonical_point_ids(question),
                        "related_chapter_ids": question.related_chapter_ids,
                        "related_knowledge_point_ids": question.related_knowledge_point_ids,
                    }
                ),
            },
        )
    return graded


def _update_mastery_from_posttest(session: Any, *, student_id: str, posttest_session_id: str) -> None:
    attempt_rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT a.correct, a.class_id, a.experiment_id, a.point_node_id,
                       a.canonical_point_id, a.source_placement_node_id, a.question_type,
                       q.difficulty, q.related_knowledge_point_ids
                FROM experiment_question_attempts a
                JOIN experiment_questions q ON q.id = a.question_id
                WHERE a.student_id = :student_id
                  AND a.metadata->>'posttest_session_id' = :posttest_session_id
                ORDER BY a.created_at, a.id
                """
            ),
            {"student_id": student_id, "posttest_session_id": posttest_session_id},
        )
        .mappings()
        .all()
    ]
    update_experiment_mastery_from_attempt_rows(
        session,
        student_id=student_id,
        class_id=next((str(row.get("class_id")) for row in attempt_rows if row.get("class_id")), None),
        attempt_rows=attempt_rows,
        evidence_kind="posttest",
        evidence_id=posttest_session_id,
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


def _answer_key(question: PosttestQuestionCandidate) -> Any:
    if question.question_type == "single_choice":
        return question.answer.get("value")
    if question.question_type == "true_false":
        return question.answer.get("value")
    if question.question_type == "fill_blank":
        return question.answer.get("accepted_answers") or []
    return question.answer


def _mastery_average(snapshot: dict[str, Any]) -> float | None:
    values = [float(item.get("mastery_score")) for item in snapshot.values() if isinstance(item, dict) and item.get("mastery_score") is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _mastery_changes(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for kp_id in sorted(set(before) | set(after)):
        before_item = before.get(kp_id) if isinstance(before.get(kp_id), dict) else {}
        after_item = after.get(kp_id) if isinstance(after.get(kp_id), dict) else {}
        before_score = float(before_item.get("mastery_score") or 0)
        after_score = float(after_item.get("mastery_score") or 0)
        content = after_item.get("content") or before_item.get("content")
        experiment_id = str(after_item.get("experiment_id") or before_item.get("experiment_id") or kp_id)
        changes.append(
            {
                "knowledge_point_id": experiment_id,
                "experiment_id": experiment_id,
                "experiment_title": content,
                "content": content,
                "before_score": round(before_score, 2),
                "after_score": round(after_score, 2),
                "delta": round(after_score - before_score, 2),
            }
        )
    return sorted(changes, key=lambda item: (item["after_score"], item["knowledge_point_id"]))


def _build_report(
    *,
    row: dict[str, Any],
    experiments: list[PosttestExperimentSummary],
    questions: list[PosttestQuestionCandidate],
    graded: list[dict[str, Any]],
    mastery_after: dict[str, Any],
) -> StudentPosttestReport:
    posttest_session_id = str(row["id"])
    correct_count = sum(1 for item in graded if item["correct"])
    total_count = len(graded)
    score = round(100 * correct_count / total_count, 2) if total_count else 0.0
    before = row.get("mastery_before") if isinstance(row.get("mastery_before"), dict) else {}
    before_avg = _mastery_average(before)
    after_avg = _mastery_average(mastery_after)
    changes = _mastery_changes(before, mastery_after)
    question_map = {question.id: question for question in questions}
    wrong_answers = [
        StudentPosttestWrongAnswer(
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
    recommendation = "本轮后测已全部答对，可以继续选择下一组实验。"
    if wrong_answers:
        recommendation = "优先复习错题对应的实验现象和解释，再继续下一组实验。"
    return StudentPosttestReport(
        session_id=posttest_session_id,
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
                        "attempt_kind": "posttest",
                        "correct_count": correct_count,
                        "total_count": total_count,
                        "score": score,
                    }
                ),
            },
        )


def submit_student_posttest(user: Any, payload: StudentPosttestSubmitRequest) -> StudentPosttestSubmitResponse:
    with db_session() as session:
        context = _load_student_context(session, user)
        _ensure_student_row(session, context)
        current = _load_open_session(session, context.student_id)
        if not current or str(current["id"]) != payload.session_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active posttest session")

        question_ids = _session_question_ids(current)
        answers = _validate_submitted_answers(question_ids, payload)
        questions_by_id = _load_questions_by_ids(session, question_ids)
        if len(questions_by_id) != len(question_ids):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Posttest question bank has changed")
        ordered_questions = [questions_by_id[question_id] for question_id in question_ids]

        posttest_session_id = str(current["id"])
        graded = _insert_attempts(
            session,
            student_id=context.student_id,
            class_id=context.class_id,
            posttest_session_id=posttest_session_id,
            questions=ordered_questions,
            answers=answers,
        )
        correct_count = sum(1 for item in graded if item["correct"])
        total_count = len(graded)
        score = round(100 * correct_count / total_count, 2) if total_count else 0.0
        experiment_ids = _session_experiment_ids(current)
        experiments = _load_experiment_summaries(session, experiment_ids)
        _update_mastery_from_posttest(session, student_id=context.student_id, posttest_session_id=posttest_session_id)
        mastery_after = _experiment_mastery_snapshot(session, student_id=context.student_id, experiments=experiments)
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
                  :student_id, 'posttest_submit', 'basic', :correct, CAST(:metadata AS jsonb), now()
                )
                """
            ),
            {
                "student_id": context.student_id,
                "correct": score >= 60 if total_count else None,
                "metadata": _json(
                    {
                        "posttest_session_id": posttest_session_id,
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
                    UPDATE student_posttest_sessions
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
                    "id": posttest_session_id,
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
        return StudentPosttestSubmitResponse(status="completed", report=report)
