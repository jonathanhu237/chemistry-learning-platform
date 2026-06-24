from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from sqlalchemy import text

from server.app.infrastructure.database import db_session
from server.app.mastery import update_mastery
from server.app.domains.assessments.mastery import update_experiment_mastery_from_attempt_rows
from server.app.domains.assessments.student_experiment import _grade_answer
from server.app.student_pretest_schemas import (
    PublicPretestQuestion,
    StudentPretestResponse,
    StudentPretestSubmitRequest,
)


AREA_ORDER = ["s区", "p区", "d区", "ds区", "f区"]
WEAKEST_AREA_PRIORITY = ["p区", "d区", "s区", "ds区", "f区"]
STAGE1_PER_AREA = 2
STAGE2_TARGET_COUNT = 10


@dataclass(frozen=True)
class StudentContext:
    student_id: str
    student_name: str
    class_id: str | None
    class_name: str | None
    user_id: str | None


@dataclass(frozen=True)
class QuestionCandidate:
    id: str
    experiment_id: str
    question_type: str
    stem: str
    options: list[Any]
    answer: dict[str, Any]
    difficulty: str
    parent_code: str
    display_order: int
    related_chapter_ids: list[str]
    related_knowledge_point_ids: list[str]
    areas: tuple[str, ...]

    @property
    def primary_area(self) -> str:
        return self.areas[0] if self.areas else ""


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


def _stable_hash(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)


def _stable_sample(items: list[QuestionCandidate], count: int, seed: str) -> list[QuestionCandidate]:
    return sorted(items, key=lambda item: (_stable_hash(f"{seed}:{item.id}"), item.id))[:count]


def _normalize_element_area(value: str | None) -> str | None:
    text_value = (value or "").replace(" ", "")
    if not text_value or "通识" in text_value:
        return None
    if "铜锌" in text_value or "ds区" in text_value:
        return "ds区"
    if "d区" in text_value or "过渡金属" in text_value:
        return "d区"
    if "镧" in text_value or "锕" in text_value or "稀土" in text_value or "f区" in text_value:
        return "f区"
    if "碱金属" in text_value or "碱土" in text_value or "s区" in text_value:
        return "s区"
    if any(token in text_value for token in ("卤族", "氧族", "氮族", "碳族", "硼族", "稀有气体", "p区", "主族")):
        return "p区"
    return None


def _ordered_areas(values: list[str | None]) -> tuple[str, ...]:
    present = {value for value in values if value in AREA_ORDER}
    return tuple(area for area in AREA_ORDER if area in present)


def _student_id_from_user(user: Any) -> str:
    return (user.student_id or user.username).strip().upper()


def _load_student_context(session: Any, user: Any) -> StudentContext:
    normalized_student_id = _student_id_from_user(user)
    row = (
        session.execute(
            text(
                """
                SELECT sp.student_id, sp.student_name, sp.class_id, sp.user_id, c.class_name
                FROM student_profiles sp
                LEFT JOIN classes c ON c.id = sp.class_id
                WHERE sp.user_id = CAST(:user_id AS uuid)
                   OR sp.student_id = :student_id
                ORDER BY CASE WHEN sp.user_id = CAST(:user_id AS uuid) THEN 0 ELSE 1 END
                LIMIT 1
                """
            ),
            {"user_id": user.id, "student_id": normalized_student_id},
        )
        .mappings()
        .first()
    )
    if row:
        return StudentContext(
            student_id=str(row["student_id"]),
            student_name=str(row["student_name"] or user.display_name),
            class_id=row.get("class_id"),
            class_name=row.get("class_name"),
            user_id=str(row["user_id"]) if row.get("user_id") else user.id,
        )
    return StudentContext(
        student_id=normalized_student_id,
        student_name=user.display_name,
        class_id=user.class_id,
        class_name=user.class_name,
        user_id=user.id,
    )


def _ensure_student_row(session: Any, context: StudentContext) -> None:
    session.execute(
        text(
            """
            INSERT INTO students (
              id, display_name, class_name, user_id, student_id, class_id, status, updated_at
            )
            VALUES (
              :student_id, :display_name, :class_name, CAST(:user_id AS uuid),
              :student_id, :class_id, 'active', now()
            )
            ON CONFLICT (id) DO UPDATE SET
              display_name = COALESCE(EXCLUDED.display_name, students.display_name),
              class_name = COALESCE(EXCLUDED.class_name, students.class_name),
              user_id = COALESCE(EXCLUDED.user_id, students.user_id),
              student_id = COALESCE(EXCLUDED.student_id, students.student_id),
              class_id = COALESCE(EXCLUDED.class_id, students.class_id),
              status = 'active',
              updated_at = now()
            """
        ),
        {
            "student_id": context.student_id,
            "display_name": context.student_name,
            "class_name": context.class_name,
            "user_id": context.user_id,
            "class_id": context.class_id,
        },
    )


def _load_area_maps(session: Any) -> tuple[dict[str, str], dict[str, tuple[str | None, str | None]], dict[str, tuple[str, ...]]]:
    chapter_areas = {
        str(row["id"]): _normalize_element_area(row.get("element_area"))
        for row in session.execute(
            text(
                """
                SELECT id, element_area
                FROM chapters
                WHERE COALESCE(content_status, 'published') = 'published'
                """
            )
        )
        .mappings()
        .all()
    }
    kp_context = {
        str(row["id"]): (
            _normalize_element_area(row.get("element_area")) or chapter_areas.get(str(row.get("chapter_id") or "")),
            str(row.get("chapter_id") or "") or None,
        )
        for row in session.execute(
            text(
                """
                SELECT id, chapter_id, element_area
                FROM knowledge_points
                WHERE COALESCE(content_status, 'published') = 'published'
                """
            )
        )
        .mappings()
        .all()
    }
    experiment_area_values: dict[str, list[str | None]] = defaultdict(list)
    for row in session.execute(
        text(
            """
            SELECT ecb.experiment_id, c.element_area
            FROM experiment_chapter_bindings ecb
            JOIN chapters c ON c.id = ecb.chapter_id
            WHERE COALESCE(c.content_status, 'published') = 'published'
            ORDER BY ecb.experiment_id,
                     CASE ecb.coverage_type WHEN 'primary' THEN 0 WHEN 'partial' THEN 1 ELSE 2 END,
                     ecb.sort_order,
                     ecb.chapter_id
            """
        )
    ).mappings():
        experiment_area_values[str(row["experiment_id"])].append(_normalize_element_area(row.get("element_area")))
    experiment_areas = {
        experiment_id: _ordered_areas(values)
        for experiment_id, values in experiment_area_values.items()
    }
    return chapter_areas, kp_context, experiment_areas


def _candidate_areas(
    *,
    experiment_id: str,
    chapter_ids: list[str],
    kp_ids: list[str],
    chapter_areas: dict[str, str],
    kp_context: dict[str, tuple[str | None, str | None]],
    experiment_areas: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    direct_areas = _ordered_areas([chapter_areas.get(chapter_id) for chapter_id in chapter_ids])
    if direct_areas:
        return direct_areas
    kp_areas = _ordered_areas([kp_context.get(kp_id, (None, None))[0] for kp_id in kp_ids])
    if kp_areas:
        return kp_areas
    return experiment_areas.get(experiment_id, ())


def _experiment_parent_code(experiment_id: str, metadata: Any) -> str:
    metadata = metadata if isinstance(metadata, dict) else {}
    return str(metadata.get("parent_code") or experiment_id)


def _load_published_pretest_candidates(session: Any) -> list[QuestionCandidate]:
    chapter_areas, kp_context, experiment_areas = _load_area_maps(session)
    candidates: list[QuestionCandidate] = []
    rows = session.execute(
        text(
            """
            SELECT q.id::text AS id, q.experiment_id, q.question_type, q.stem, q.options,
                   q.answer, q.difficulty, q.related_chapter_ids, q.related_knowledge_point_ids,
                   fe.metadata AS experiment_metadata, fe.display_order
            FROM experiment_questions q
            JOIN formal_experiments fe ON fe.id = q.experiment_id
            WHERE q.status = 'published'
              AND q.question_type = 'single_choice'
            ORDER BY q.created_at, q.id
            """
        )
    ).mappings()
    for row in rows:
        chapter_ids = [str(item) for item in _as_list(row.get("related_chapter_ids")) if str(item).strip()]
        kp_ids = [str(item) for item in _as_list(row.get("related_knowledge_point_ids")) if str(item).strip()]
        areas = _candidate_areas(
            experiment_id=str(row["experiment_id"]),
            chapter_ids=chapter_ids,
            kp_ids=kp_ids,
            chapter_areas=chapter_areas,
            kp_context=kp_context,
            experiment_areas=experiment_areas,
        )
        if not areas:
            continue
        options = row.get("options") if isinstance(row.get("options"), list) else []
        if len(options) < 2:
            continue
        answer = row.get("answer") if isinstance(row.get("answer"), dict) else {}
        candidates.append(
            QuestionCandidate(
                id=str(row["id"]),
                experiment_id=str(row["experiment_id"]),
                question_type=str(row["question_type"]),
                stem=str(row["stem"]),
                options=options,
                answer=answer,
                difficulty=str(row.get("difficulty") or "basic"),
                parent_code=_experiment_parent_code(str(row["experiment_id"]), row.get("experiment_metadata")),
                display_order=int(row.get("display_order") or 0),
                related_chapter_ids=chapter_ids,
                related_knowledge_point_ids=kp_ids,
                areas=areas,
            )
        )
    return candidates


def _load_questions_by_ids(session: Any, question_ids: list[str]) -> dict[str, QuestionCandidate]:
    if not question_ids:
        return {}
    chapter_areas, kp_context, experiment_areas = _load_area_maps(session)
    rows = session.execute(
        text(
            """
            SELECT q.id::text AS id, q.experiment_id, q.question_type, q.stem, q.options,
                   q.answer, q.difficulty, q.related_chapter_ids, q.related_knowledge_point_ids,
                   fe.metadata AS experiment_metadata, fe.display_order
            FROM experiment_questions q
            JOIN formal_experiments fe ON fe.id = q.experiment_id
            WHERE q.id::text = ANY(:question_ids)
            """
        ),
        {"question_ids": question_ids},
    ).mappings()
    questions: dict[str, QuestionCandidate] = {}
    for row in rows:
        chapter_ids = [str(item) for item in _as_list(row.get("related_chapter_ids")) if str(item).strip()]
        kp_ids = [str(item) for item in _as_list(row.get("related_knowledge_point_ids")) if str(item).strip()]
        areas = _candidate_areas(
            experiment_id=str(row["experiment_id"]),
            chapter_ids=chapter_ids,
            kp_ids=kp_ids,
            chapter_areas=chapter_areas,
            kp_context=kp_context,
            experiment_areas=experiment_areas,
        )
        questions[str(row["id"])] = QuestionCandidate(
            id=str(row["id"]),
            experiment_id=str(row["experiment_id"]),
            question_type=str(row["question_type"]),
            stem=str(row["stem"]),
            options=row.get("options") if isinstance(row.get("options"), list) else [],
            answer=row.get("answer") if isinstance(row.get("answer"), dict) else {},
            difficulty=str(row.get("difficulty") or "basic"),
            parent_code=_experiment_parent_code(str(row["experiment_id"]), row.get("experiment_metadata")),
            display_order=int(row.get("display_order") or 0),
            related_chapter_ids=chapter_ids,
            related_knowledge_point_ids=kp_ids,
            areas=areas,
        )
    return questions


def _area_pools(candidates: list[QuestionCandidate]) -> dict[str, list[QuestionCandidate]]:
    pools: dict[str, list[QuestionCandidate]] = {area: [] for area in AREA_ORDER}
    for candidate in candidates:
        for area in candidate.areas:
            pools[area].append(candidate)
    return pools


def _select_stage1_questions(
    candidates: list[QuestionCandidate],
    *,
    student_id: str,
) -> tuple[list[QuestionCandidate], dict[str, str], dict[str, Any]]:
    pools = _area_pools(candidates)
    selected: list[QuestionCandidate] = []
    question_areas: dict[str, str] = {}
    warnings: dict[str, Any] = {"missing_areas": [], "underfilled_areas": {}}
    for area in AREA_ORDER:
        pool = pools[area]
        if not pool:
            warnings["missing_areas"].append(area)
            continue
        if len(pool) < STAGE1_PER_AREA:
            warnings["underfilled_areas"][area] = len(pool)
        for question in _stable_sample(pool, STAGE1_PER_AREA, f"{student_id}:pretest:stage1:{area}"):
            selected.append(question)
            question_areas[question.id] = area
    return selected, question_areas, warnings


def _group_key(question: QuestionCandidate) -> str:
    return f"{question.parent_code}:{question.experiment_id}"


def _balanced_stage2_sample(pool: list[QuestionCandidate], *, seed: str, count: int) -> list[QuestionCandidate]:
    groups: dict[str, list[QuestionCandidate]] = defaultdict(list)
    for question in pool:
        groups[_group_key(question)].append(question)
    ordered_groups = {
        key: _stable_sample(items, len(items), f"{seed}:{key}")
        for key, items in sorted(groups.items())
    }
    selected: list[QuestionCandidate] = []
    used: set[str] = set()
    while len(selected) < count:
        progressed = False
        for key in list(ordered_groups):
            items = ordered_groups[key]
            while items and items[0].id in used:
                items.pop(0)
            if not items:
                continue
            question = items.pop(0)
            selected.append(question)
            used.add(question.id)
            progressed = True
            if len(selected) >= count:
                break
        if not progressed:
            break
    return selected


def _select_stage2_questions(
    candidates: list[QuestionCandidate],
    *,
    student_id: str,
    weakest_area: str,
) -> tuple[list[QuestionCandidate], dict[str, str], dict[str, Any]]:
    pool = [candidate for candidate in candidates if weakest_area in candidate.areas]
    if not pool:
        return [], {}, {"missing_area": weakest_area}

    selected = _balanced_stage2_sample(
        pool,
        seed=f"{student_id}:pretest:stage2:{weakest_area}",
        count=STAGE2_TARGET_COUNT,
    )

    selected = selected[:STAGE2_TARGET_COUNT]
    question_areas = {question.id: weakest_area for question in selected}
    warnings: dict[str, Any] = {}
    if len(selected) < STAGE2_TARGET_COUNT:
        warnings["underfilled_area"] = {"area": weakest_area, "count": len(selected)}
    return selected, question_areas, warnings


def _question_ids(questions: list[QuestionCandidate]) -> list[str]:
    return [question.id for question in questions]


def _stage_ids(row: dict[str, Any], stage: int) -> list[str]:
    key = "stage1_question_ids" if stage == 1 else "stage2_question_ids"
    return [str(item) for item in _as_list(row.get(key)) if str(item).strip()]


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata")
    return value if isinstance(value, dict) else {}


def _public_question(question: QuestionCandidate, area: str | None = None) -> PublicPretestQuestion:
    return PublicPretestQuestion(
        id=question.id,
        question_type=question.question_type,  # type: ignore[arg-type]
        stem=question.stem,
        options=question.options,
        area=area or question.primary_area,
        related_chapter_ids=question.related_chapter_ids,
        related_knowledge_point_ids=question.related_knowledge_point_ids,
    )


def _response_for_session(session: Any, row: dict[str, Any]) -> StudentPretestResponse:
    if row.get("status") == "completed":
        return StudentPretestResponse(status="completed", session_id=str(row["id"]), stage=None, questions=[])

    stage = int(row.get("current_stage") or 1)
    question_ids = _stage_ids(row, stage)
    questions = _load_questions_by_ids(session, question_ids)
    metadata = _metadata(row)
    area_key = "stage1_question_areas" if stage == 1 else "stage2_question_areas"
    area_map = metadata.get(area_key) if isinstance(metadata.get(area_key), dict) else {}
    public_questions = [
        _public_question(questions[question_id], area=str(area_map.get(question_id) or questions[question_id].primary_area))
        for question_id in question_ids
        if question_id in questions
    ]
    return StudentPretestResponse(status="in_progress", session_id=str(row["id"]), stage=stage, questions=public_questions)


def _load_current_session(session: Any, student_id: str) -> dict[str, Any] | None:
    row = (
        session.execute(
            text(
                """
                SELECT *
                FROM student_pretest_sessions
                WHERE student_id = :student_id
                  AND status IN ('in_progress', 'completed')
                ORDER BY CASE status WHEN 'completed' THEN 0 ELSE 1 END, created_at DESC
                LIMIT 1
                """
            ),
            {"student_id": student_id},
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


def start_student_pretest(user: Any) -> StudentPretestResponse:
    with db_session() as session:
        context = _load_student_context(session, user)
        _ensure_student_row(session, context)
        existing = _load_current_session(session, context.student_id)
        if existing:
            return _response_for_session(session, existing)

        candidates = _load_published_pretest_candidates(session)
        stage1, stage1_areas, stage1_warnings = _select_stage1_questions(candidates, student_id=context.student_id)
        if not stage1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pretest question bank is not configured")
        metadata = {
            "stage1_question_areas": stage1_areas,
            "warnings": {"stage1": stage1_warnings},
        }
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO student_pretest_sessions (
                      student_id, class_id, status, current_stage, stage1_question_ids, metadata
                    )
                    VALUES (
                      :student_id, :class_id, 'in_progress', 1,
                      CAST(:stage1_question_ids AS jsonb), CAST(:metadata AS jsonb)
                    )
                    RETURNING *
                    """
                ),
                {
                    "student_id": context.student_id,
                    "class_id": context.class_id,
                    "stage1_question_ids": _json_array(_question_ids(stage1)),
                    "metadata": _json(metadata),
                },
            )
            .mappings()
            .one()
        )
        return _response_for_session(session, dict(row))


def _validate_submitted_answers(question_ids: list[str], payload: StudentPretestSubmitRequest) -> dict[str, Any]:
    expected = set(question_ids)
    submitted = {answer.question_id for answer in payload.answers}
    if len(payload.answers) != len(submitted) or submitted != expected:
        missing = sorted(expected - submitted)
        extra = sorted(submitted - expected)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Submitted answers must match the current stage questions", "missing": missing, "extra": extra},
        )
    return {answer.question_id: answer.answer for answer in payload.answers}


def _score_by_area(graded: list[dict[str, Any]]) -> dict[str, float | None]:
    scores: dict[str, float | None] = {}
    for area in AREA_ORDER:
        area_answers = [item for item in graded if item["area"] == area]
        if not area_answers:
            scores[area] = None
            continue
        scores[area] = sum(1 for item in area_answers if item["correct"]) / len(area_answers)
    return scores


def _weakest_area(area_scores: dict[str, float | None]) -> str:
    available = {area: score for area, score in area_scores.items() if score is not None}
    if not available:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pretest stage 1 has no gradable area")
    lowest = min(score for score in available.values() if score is not None)
    return next(area for area in WEAKEST_AREA_PRIORITY if available.get(area) == lowest)


def _insert_attempts(
    session: Any,
    *,
    context: StudentContext,
    pretest_session_id: str,
    stage: int,
    questions: list[QuestionCandidate],
    answers: dict[str, Any],
    area_map: dict[str, str],
) -> list[dict[str, Any]]:
    graded: list[dict[str, Any]] = []
    for question in questions:
        submitted = answers[question.id]
        correct = _grade_answer(question.question_type, question.answer, submitted)
        area = area_map.get(question.id) or question.primary_area
        graded.append({"question": question, "correct": correct, "area": area, "submitted": submitted})
        session.execute(
            text(
                """
                INSERT INTO experiment_question_attempts (
                  student_id, class_id, experiment_id, question_id, question_type,
                  submitted_answer, correct, score, attempt_kind, metadata
                )
                VALUES (
                  :student_id, :class_id, :experiment_id, CAST(:question_id AS uuid), :question_type,
                  CAST(:submitted_answer AS jsonb), :correct, :score, :attempt_kind, CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "student_id": context.student_id,
                "class_id": context.class_id,
                "experiment_id": question.experiment_id,
                "question_id": question.id,
                "question_type": question.question_type,
                "submitted_answer": _json({"value": submitted}),
                "correct": correct,
                "score": 1 if correct else 0,
                "attempt_kind": f"pretest_stage{stage}",
                "metadata": _json(
                    {
                        "pretest_session_id": pretest_session_id,
                        "pretest_stage": stage,
                        "area": area,
                        "related_chapter_ids": question.related_chapter_ids,
                        "related_knowledge_point_ids": question.related_knowledge_point_ids,
                    }
                ),
            },
        )
    return graded


def _record_stage_event(
    session: Any,
    *,
    context: StudentContext,
    pretest_session_id: str,
    stage: int,
    graded: list[dict[str, Any]],
) -> None:
    total = len(graded)
    correct_count = sum(1 for item in graded if item["correct"])
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
            "event_type": f"pretest_stage{stage}_submit",
            "correct": (correct_count / total) >= 0.6 if total else None,
            "metadata": _json(
                {
                    "pretest_session_id": pretest_session_id,
                    "stage": stage,
                    "correct_count": correct_count,
                    "total_count": total,
                }
            ),
        },
    )


def _update_mastery_from_session(session: Any, *, student_id: str, pretest_session_id: str) -> None:
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
                  AND a.metadata->>'pretest_session_id' = :pretest_session_id
                ORDER BY a.created_at, a.id
                """
            ),
            {"student_id": student_id, "pretest_session_id": pretest_session_id},
        )
        .mappings()
        .all()
    ]
    update_experiment_mastery_from_attempt_rows(
        session,
        student_id=student_id,
        class_id=next((str(row.get("class_id")) for row in attempt_rows if row.get("class_id")), None),
        attempt_rows=attempt_rows,
        evidence_kind="pretest",
        evidence_id=pretest_session_id,
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
        for row in session.execute(
            text("SELECT id FROM knowledge_points WHERE id = ANY(:kp_ids)"),
            {"kp_ids": kp_ids},
        ).mappings()
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


def submit_student_pretest_stage(user: Any, payload: StudentPretestSubmitRequest) -> StudentPretestResponse:
    with db_session() as session:
        context = _load_student_context(session, user)
        _ensure_student_row(session, context)
        current = _load_current_session(session, context.student_id)
        if not current or current.get("status") != "in_progress":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active pretest session")
        current_stage = int(current.get("current_stage") or 0)
        if payload.stage != current_stage:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pretest stage is no longer active")

        question_ids = _stage_ids(current, current_stage)
        answers = _validate_submitted_answers(question_ids, payload)
        questions_by_id = _load_questions_by_ids(session, question_ids)
        if len(questions_by_id) != len(question_ids):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pretest question bank has changed")

        metadata = _metadata(current)
        area_key = "stage1_question_areas" if current_stage == 1 else "stage2_question_areas"
        area_map = {
            str(question_id): str(area)
            for question_id, area in (metadata.get(area_key) if isinstance(metadata.get(area_key), dict) else {}).items()
        }
        ordered_questions = [questions_by_id[question_id] for question_id in question_ids]
        pretest_session_id = str(current["id"])
        graded = _insert_attempts(
            session,
            context=context,
            pretest_session_id=pretest_session_id,
            stage=current_stage,
            questions=ordered_questions,
            answers=answers,
            area_map=area_map,
        )
        _record_stage_event(
            session,
            context=context,
            pretest_session_id=pretest_session_id,
            stage=current_stage,
            graded=graded,
        )

        if current_stage == 1:
            area_scores = _score_by_area(graded)
            weakest_area = _weakest_area(area_scores)
            candidates = _load_published_pretest_candidates(session)
            stage2, stage2_areas, stage2_warnings = _select_stage2_questions(
                candidates,
                student_id=context.student_id,
                weakest_area=weakest_area,
            )
            if not stage2:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Pretest question bank is not configured for {weakest_area}",
                )
            metadata["stage1_area_scores"] = area_scores
            metadata["stage2_question_areas"] = stage2_areas
            warnings = metadata.setdefault("warnings", {})
            if isinstance(warnings, dict):
                warnings["stage2"] = stage2_warnings
            row = (
                session.execute(
                    text(
                        """
                        UPDATE student_pretest_sessions
                        SET current_stage = 2,
                            stage2_question_ids = CAST(:stage2_question_ids AS jsonb),
                            weakest_area = :weakest_area,
                            metadata = CAST(:metadata AS jsonb),
                            stage1_submitted_at = now(),
                            updated_at = now()
                        WHERE id = CAST(:id AS uuid)
                        RETURNING *
                        """
                    ),
                    {
                        "id": pretest_session_id,
                        "stage2_question_ids": _json_array(_question_ids(stage2)),
                        "weakest_area": weakest_area,
                        "metadata": _json(metadata),
                    },
                )
                .mappings()
                .one()
            )
            return _response_for_session(session, dict(row))

        _update_mastery_from_session(session, student_id=context.student_id, pretest_session_id=pretest_session_id)
        row = (
            session.execute(
                text(
                    """
                    UPDATE student_pretest_sessions
                    SET status = 'completed',
                        current_stage = NULL,
                        completed_at = now(),
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    RETURNING *
                    """
                ),
                {"id": pretest_session_id},
            )
            .mappings()
            .one()
        )
        return _response_for_session(session, dict(row))
