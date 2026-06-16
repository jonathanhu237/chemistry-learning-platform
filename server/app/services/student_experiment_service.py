from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from server.app.database import db_session
from server.app.experiment_admin_schemas import ExperimentQuestionSubmitRequest


TRUE_FALSE_TRUE_VALUES = {"true", "t", "1", "yes", "y", "正确", "对"}
TRUE_FALSE_FALSE_VALUES = {"false", "f", "0", "no", "n", "错误", "错"}


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _normalize_answer(question_type: str, answer: Any) -> dict[str, Any]:
    if question_type == "single_choice":
        value = str(answer.get("value") if isinstance(answer, dict) else answer).strip()
        if not value:
            raise ValueError("single_choice answer is required")
        return {"value": value}
    if question_type == "true_false":
        raw = answer.get("value") if isinstance(answer, dict) else answer
        if isinstance(raw, bool):
            value = raw
        else:
            normalized = str(raw).strip().lower()
            if normalized in TRUE_FALSE_TRUE_VALUES:
                value = True
            elif normalized in TRUE_FALSE_FALSE_VALUES:
                value = False
            else:
                raise ValueError("true_false answer must be true or false")
        return {"value": value}
    if question_type == "fill_blank":
        raw = answer.get("accepted_answers") if isinstance(answer, dict) else answer
        values = raw if isinstance(raw, list) else [raw]
        accepted = [str(item).strip() for item in values if str(item).strip()]
        if not accepted:
            raise ValueError("fill_blank accepted_answers are required")
        return {"accepted_answers": accepted, "match": "normalized_exact"}
    raise ValueError("unsupported question_type")


def _grade_answer(question_type: str, expected: dict[str, Any], submitted: Any) -> bool:
    if question_type == "single_choice":
        return str(submitted).strip().lower() == str(expected.get("value") or "").strip().lower()
    if question_type == "true_false":
        try:
            submitted_norm = _normalize_answer("true_false", submitted)["value"]
        except ValueError:
            return False
        return bool(submitted_norm) is bool(expected.get("value"))
    if question_type == "fill_blank":
        submitted_text = str(submitted).strip().lower()
        return submitted_text in {str(item).strip().lower() for item in expected.get("accepted_answers") or []}
    return False


def _single_choice_label(submitted: Any) -> str | None:
    raw = submitted.get("value") if isinstance(submitted, dict) else submitted
    label = str(raw or "").strip()
    return label.upper() if label else None


def _attempt_diagnostic_metadata(question: dict[str, Any], submitted: Any, correct: bool) -> dict[str, Any]:
    question_metadata = question.get("metadata") if isinstance(question.get("metadata"), dict) else {}
    primary_point_keys = [
        str(item)
        for item in question_metadata.get("primary_point_keys") or []
        if str(item).strip()
    ]
    primary_points = [
        item
        for item in question_metadata.get("primary_points") or []
        if isinstance(item, dict) and item.get("point_key")
    ]
    selected_label = _single_choice_label(submitted) if question.get("question_type") == "single_choice" else None
    option_links = [
        item
        for item in question_metadata.get("option_links") or []
        if isinstance(item, dict)
    ]
    selected_option_link = None
    if selected_label:
        selected_option_link = next(
            (
                item
                for item in option_links
                if str(item.get("label") or "").strip().upper() == selected_label
            ),
            None,
        )
    return {
        "point_aware_question_bank": bool(question_metadata.get("point_aware_question_bank")),
        "primary_point_keys": primary_point_keys,
        "primary_points": primary_points,
        "coverage_tags": list(question_metadata.get("coverage_tags") or []),
        "selected_option_label": selected_label,
        "selected_option_link": selected_option_link,
        "diagnostic_role": selected_option_link.get("role") if isinstance(selected_option_link, dict) else None,
        "correct": correct,
    }


def submit_experiment_question_attempt(payload: ExperimentQuestionSubmitRequest) -> dict[str, Any]:
    answer_lookup = {answer.question_id: answer.answer for answer in payload.answers}
    with db_session() as session:
        student = (
            session.execute(
                text(
                    """
                    SELECT sp.student_id, sp.student_name, sp.class_id, sp.user_id, c.class_name
                    FROM student_profiles sp
                    LEFT JOIN classes c ON c.id = sp.class_id
                    WHERE sp.student_id = :student_id
                    UNION
                    SELECT re.student_id, re.student_name, re.class_id, NULL::uuid AS user_id, c.class_name
                    FROM roster_entries re
                    LEFT JOIN classes c ON c.id = re.class_id
                    WHERE re.student_id = :student_id
                      AND re.status <> 'disabled'
                    ORDER BY class_id NULLS LAST
                    LIMIT 1
                    """
                ),
                {"student_id": payload.student_id},
            )
            .mappings()
            .first()
        )
        class_id = student["class_id"] if student else None
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
                "student_id": payload.student_id,
                "display_name": student["student_name"] if student else payload.student_id,
                "class_name": student["class_name"] if student else None,
                "user_id": str(student["user_id"]) if student and student.get("user_id") else None,
                "class_id": class_id,
            },
        )
        questions = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT *
                    FROM experiment_questions
                    WHERE experiment_id = :experiment_id
                      AND status = 'published'
                      AND id = ANY(:question_ids)
                    """
                ),
                {"experiment_id": payload.experiment_id, "question_ids": list(answer_lookup.keys())},
            )
            .mappings()
            .all()
        ]
        correct_count = 0
        submitted_point_keys: set[str] = set()
        submitted_option_links: list[dict[str, Any]] = []
        for question in questions:
            submitted = answer_lookup.get(str(question["id"]))
            correct = _grade_answer(question["question_type"], question["answer"], submitted)
            correct_count += 1 if correct else 0
            attempt_metadata = _attempt_diagnostic_metadata(question, submitted, correct)
            submitted_point_keys.update(attempt_metadata.get("primary_point_keys") or [])
            if isinstance(attempt_metadata.get("selected_option_link"), dict):
                submitted_option_links.append(attempt_metadata["selected_option_link"])
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
                    "student_id": payload.student_id,
                    "class_id": class_id,
                    "experiment_id": payload.experiment_id,
                    "question_id": str(question["id"]),
                    "question_type": question["question_type"],
                    "submitted_answer": _json({"value": submitted}),
                    "correct": correct,
                    "score": 1 if correct else 0,
                    "attempt_kind": payload.attempt_kind,
                    "metadata": _json(attempt_metadata),
                },
            )
        total = len(questions)
        score = round(100 * correct_count / total, 2) if total else 0
        status_value = "completed" if total and score >= 60 else ("needs_attention" if total else "in_progress")
        session.execute(
            text(
                """
                INSERT INTO student_experiment_progress (
                  student_id, class_id, experiment_id, status, completion_percent,
                  best_score, last_activity_at, completed_at, metadata, updated_at
                )
                VALUES (
                  :student_id, :class_id, :experiment_id, :status, :completion_percent,
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
                "student_id": payload.student_id,
                "class_id": class_id,
                "experiment_id": payload.experiment_id,
                "status": status_value,
                "completion_percent": 100 if total else 20,
                "score": score,
                "metadata": _json({"correct_count": correct_count, "total_count": total, "attempt_kind": payload.attempt_kind}),
            },
        )
        primary_chapter = session.execute(
            text(
                """
                SELECT chapter_id
                FROM experiment_chapter_bindings
                WHERE experiment_id = :experiment_id
                ORDER BY CASE coverage_type WHEN 'primary' THEN 0 WHEN 'partial' THEN 1 ELSE 2 END, sort_order
                LIMIT 1
                """
            ),
            {"experiment_id": payload.experiment_id},
        ).scalar()
        session.execute(
            text(
                """
                INSERT INTO student_events (
                  student_id, event_type, chapter_id, experiment_id, difficulty,
                  correct, metadata, created_at
                )
                VALUES (
                  :student_id, 'experiment_question_submit', :chapter_id, :experiment_id,
                  'basic', :correct, CAST(:metadata AS jsonb), now()
                )
                """
            ),
            {
                "student_id": payload.student_id,
                "chapter_id": primary_chapter,
                "experiment_id": payload.experiment_id,
                "correct": score >= 60 if total else None,
                "metadata": _json(
                    {
                        "score": score,
                        "correct_count": correct_count,
                        "total_count": total,
                        "point_keys": sorted(submitted_point_keys),
                        "selected_option_links": submitted_option_links,
                    }
                ),
            },
        )
    return {"score": score, "correct_count": correct_count, "total_count": total}
