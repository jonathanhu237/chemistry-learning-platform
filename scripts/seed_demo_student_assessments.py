from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from sqlalchemy import bindparam, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.seed_demo_identities import DEFAULT_SEED_PATH, load_seed
from server.app.domains.assessments.posttest import _answer_key, _load_questions_by_ids
from server.app.domains.assessments.smart_assessment import (
    start_student_smart_assessment,
    submit_student_smart_assessment,
)
from server.app.domains.student_legacy.reports import (
    _as_dict_list,
    _generated_text,
    _insert_report,
    _legacy_mistake_text,
    _legacy_summary_text,
    _model_dump,
    _report_title,
    _student_id,
)
from server.app.infrastructure.database import apply_migrations, db_session
from server.app.student_smart_assessment_schemas import (
    StudentSmartAssessmentAnswer,
    StudentSmartAssessmentSubmitRequest,
)

SEED_SOURCE = "demo_student_assessments_v1"
EXPECTED_STUDENTS = 150
SHOWCASE_STUDENT_ID = "26320001"
SHOWCASE_MASTERY_PROFILE_SOURCE = "demo_showcase_zhangsan_mastery_v1"
SHOWCASE_CHAPTER_MASTERY_TARGETS = {
    "CH13": 29.0,
    "CH14": 84.0,
    "CH15": 37.0,
    "CH16": 76.0,
    "CH17": 24.0,
    "CH18": 88.0,
    "CH19": 66.0,
    "CH20": 41.0,
    "CH22": 92.0,
}


@dataclass(frozen=True)
class DemoStudent:
    student_id: str
    username: str
    student_name: str
    class_id: str
    class_name: str | None
    class_index: int
    roster_index: int


def _json_param(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _stable_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16)


def _seed_classes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    classes = payload.get("classes")
    if isinstance(classes, list) and classes:
        return [item for item in classes if isinstance(item, dict)]
    klass = payload.get("class")
    return [klass] if isinstance(klass, dict) else []


def seed_students(payload: dict[str, Any]) -> list[DemoStudent]:
    classes = _seed_classes(payload)
    class_names = {
        str(klass.get("id") or "").strip(): str(klass.get("class_name") or "").strip() or None
        for klass in classes
        if str(klass.get("id") or "").strip()
    }
    class_order = {class_id: index + 1 for index, class_id in enumerate(class_names)}
    default_class_id = str((payload.get("class") or {}).get("id") or "").strip()
    students: list[DemoStudent] = []
    for roster_index, student in enumerate(payload.get("students") or [], start=1):
        if not isinstance(student, dict):
            continue
        class_id = str(student.get("class_id") or default_class_id).strip()
        student_id = str(student.get("student_id") or "").strip().upper()
        if not student_id:
            continue
        students.append(
            DemoStudent(
                student_id=student_id,
                username=str(student.get("username") or student_id).strip(),
                student_name=str(student.get("student_name") or student_id).strip(),
                class_id=class_id,
                class_name=class_names.get(class_id),
                class_index=class_order.get(class_id, 1),
                roster_index=roster_index,
            )
        )
    return students


def target_correct_ratio(student: DemoStudent) -> float:
    class_base = {
        1: 0.82,
        2: 0.74,
        3: 0.66,
        4: 0.58,
        5: 0.50,
    }.get(student.class_index, 0.64)
    student_offset = (((student.roster_index - 1) % 10) - 4.5) * 0.025
    return max(0.35, min(0.95, class_base + student_offset))


def should_answer_correct(student: DemoStudent, question_index: int) -> bool:
    bucket = (student.roster_index * 37 + question_index * 17 + student.class_index * 11) % 100
    return bucket < round(target_correct_ratio(student) * 100)


def correct_answer(question: Any) -> Any:
    answer = _answer_key(question)
    if question.question_type == "fill_blank" and isinstance(answer, list):
        return str(answer[0]).strip() if answer else ""
    return answer


def wrong_answer(question: Any) -> Any:
    expected = correct_answer(question)
    if question.question_type == "single_choice":
        expected_text = str(expected or "").strip().lower()
        for option in question.options:
            if isinstance(option, dict):
                raw = option.get("value") or option.get("label") or option.get("key")
            else:
                raw = option
            candidate = str(raw or "").strip()
            if candidate and candidate.lower() != expected_text:
                return candidate
        return "__wrong_choice__"
    if question.question_type == "true_false":
        if isinstance(expected, bool):
            return not expected
        normalized = str(expected or "").strip().lower()
        return "false" if normalized in {"true", "t", "1", "yes", "y", "正确", "对"} else "true"
    if question.question_type == "fill_blank":
        return "模拟错误答案"
    return None


def build_answers(student: DemoStudent, questions: list[Any]) -> list[StudentSmartAssessmentAnswer]:
    answers: list[StudentSmartAssessmentAnswer] = []
    for index, question in enumerate(questions):
        value = correct_answer(question) if should_answer_correct(student, index) else wrong_answer(question)
        answers.append(StudentSmartAssessmentAnswer(question_id=question.id, answer=value))
    return answers


def showcase_mastery_score(chapter_id: str, point_node_id: str) -> float:
    target = SHOWCASE_CHAPTER_MASTERY_TARGETS.get(chapter_id, 50.0)
    jitter = (_stable_int(f"{chapter_id}:{point_node_id}:score") % 1301) / 100.0 - 6.5
    return round(max(6.0, min(96.0, target + jitter)), 1)


def showcase_evidence_count(chapter_id: str, point_node_id: str) -> int:
    return 8 + (_stable_int(f"{chapter_id}:{point_node_id}:evidence") % 13)


def _student_ids(students: list[DemoStudent]) -> list[str]:
    return [student.student_id for student in students]


def _expanded(sql: str, name: str) -> Any:
    return text(sql).bindparams(bindparam(name, expanding=True))


def cleanup_seed_generated_data(students: list[DemoStudent], *, reset_mastery: bool) -> dict[str, int]:
    student_ids = _student_ids(students)
    if not student_ids:
        return {
            "assessment_reports": 0,
            "question_attempts": 0,
            "student_events": 0,
            "smart_sessions": 0,
            "open_sessions_abandoned": 0,
            "point_mastery": 0,
            "experiment_progress": 0,
            "legacy_mastery": 0,
        }

    with db_session() as session:
        session_ids = [
            str(row["id"])
            for row in session.execute(
                _expanded(
                    """
                    SELECT id::text AS id
                    FROM student_smart_assessment_sessions
                    WHERE student_id IN :student_ids
                      AND (
                        metadata->>'seed_source' = :seed_source
                        OR assessment_mode = 'smart'
                      )
                    """,
                    "student_ids",
                ),
                {"student_ids": student_ids, "seed_source": SEED_SOURCE},
            ).mappings()
        ]
        counts = {
            "assessment_reports": 0,
            "question_attempts": 0,
            "student_events": 0,
            "smart_sessions": 0,
            "open_sessions_abandoned": 0,
            "point_mastery": 0,
            "experiment_progress": 0,
            "legacy_mastery": 0,
        }
        if session_ids:
            counts["assessment_reports"] = session.execute(
                _expanded(
                    """
                    DELETE FROM student_assessment_reports
                    WHERE source_session_id::text IN :session_ids
                    """,
                    "session_ids",
                ),
                {"session_ids": session_ids},
            ).rowcount or 0
            counts["question_attempts"] = session.execute(
                _expanded(
                    """
                    DELETE FROM experiment_question_attempts
                    WHERE metadata->>'smart_assessment_session_id' IN :session_ids
                    """,
                    "session_ids",
                ),
                {"session_ids": session_ids},
            ).rowcount or 0
            counts["student_events"] = session.execute(
                _expanded(
                    """
                    DELETE FROM student_events
                    WHERE metadata->>'smart_assessment_session_id' IN :session_ids
                    """,
                    "session_ids",
                ),
                {"session_ids": session_ids},
            ).rowcount or 0
            counts["smart_sessions"] = session.execute(
                _expanded(
                    """
                    DELETE FROM student_smart_assessment_sessions
                    WHERE id::text IN :session_ids
                    """,
                    "session_ids",
                ),
                {"session_ids": session_ids},
            ).rowcount or 0

        counts["open_sessions_abandoned"] = session.execute(
            _expanded(
                """
                UPDATE student_smart_assessment_sessions
                SET status = 'abandoned',
                    metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata AS jsonb),
                    updated_at = now()
                WHERE student_id IN :student_ids
                  AND status = 'in_progress'
                """,
                "student_ids",
            ),
            {
                "student_ids": student_ids,
                "metadata": _json_param({"abandoned_by_seed_source": SEED_SOURCE}),
            },
        ).rowcount or 0

        if reset_mastery:
            counts["point_mastery"] = session.execute(
                _expanded("DELETE FROM student_point_mastery WHERE student_id IN :student_ids", "student_ids"),
                {"student_ids": student_ids},
            ).rowcount or 0
            counts["experiment_progress"] = session.execute(
                _expanded("DELETE FROM student_experiment_progress WHERE student_id IN :student_ids", "student_ids"),
                {"student_ids": student_ids},
            ).rowcount or 0
            counts["legacy_mastery"] = session.execute(
                _expanded("DELETE FROM student_mastery WHERE student_id IN :student_ids", "student_ids"),
                {"student_ids": student_ids},
            ).rowcount or 0
    return counts


def _load_user_row(student: DemoStudent) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT au.id::text AS id, au.username, au.display_name, au.role, au.status,
                           sp.student_id, sp.student_name, sp.class_id, c.class_name
                    FROM student_profiles sp
                    JOIN app_users au ON au.id = sp.user_id
                    LEFT JOIN classes c ON c.id = sp.class_id
                    WHERE sp.student_id = :student_id
                      AND au.role = 'student'
                      AND au.status = 'active'
                    LIMIT 1
                    """
                ),
                {"student_id": student.student_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise RuntimeError(f"Active seed student account is missing: {student.student_id}")
    return dict(row)


def _user_from_row(row: dict[str, Any]) -> Any:
    return SimpleNamespace(
        id=str(row["id"]),
        username=str(row["username"]),
        role=str(row["role"]),
        status=str(row["status"]),
        display_name=str(row.get("display_name") or row.get("student_name") or row["username"]),
        student_id=str(row["student_id"]),
        class_id=row.get("class_id"),
        class_name=row.get("class_name"),
    )


def _questions_for_response(question_ids: list[str]) -> list[Any]:
    with db_session() as session:
        questions_by_id = _load_questions_by_ids(session, question_ids)
    missing = [question_id for question_id in question_ids if question_id not in questions_by_id]
    if missing:
        raise RuntimeError(f"Published question rows are missing: {', '.join(missing[:5])}")
    return [questions_by_id[question_id] for question_id in question_ids]


def mark_seed_metadata(student: DemoStudent, session_id: str) -> None:
    metadata = {
        "seed_owned": True,
        "seed_source": SEED_SOURCE,
        "seed_student_id": student.student_id,
        "seed_class_id": student.class_id,
    }
    with db_session() as session:
        session.execute(
            text(
                """
                UPDATE student_smart_assessment_sessions
                SET metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata AS jsonb),
                    updated_at = now()
                WHERE id = CAST(:session_id AS uuid)
                """
            ),
            {"session_id": session_id, "metadata": _json_param(metadata)},
        )
        session.execute(
            text(
                """
                UPDATE experiment_question_attempts
                SET metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata AS jsonb)
                WHERE metadata->>'smart_assessment_session_id' = :session_id
                """
            ),
            {"session_id": session_id, "metadata": _json_param(metadata)},
        )
        session.execute(
            text(
                """
                UPDATE student_events
                SET metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata AS jsonb)
                WHERE metadata->>'smart_assessment_session_id' = :session_id
                """
            ),
            {"session_id": session_id, "metadata": _json_param(metadata)},
        )
        session.execute(
            text(
                """
                UPDATE student_assessment_reports
                SET payload = COALESCE(payload, '{}'::jsonb) || jsonb_build_object('metadata', CAST(:metadata AS jsonb)),
                    prompt_snapshot = COALESCE(prompt_snapshot, '{}'::jsonb) || CAST(:metadata AS jsonb),
                    updated_at = now()
                WHERE source_session_id = CAST(:session_id AS uuid)
                """
            ),
            {"session_id": session_id, "metadata": _json_param(metadata)},
        )


def seed_showcase_mastery_profile(student: DemoStudent) -> dict[str, Any]:
    if student.student_id != SHOWCASE_STUDENT_ID:
        return {"updated": False, "student_id": student.student_id}

    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT n.id AS point_node_id,
                           n.chapter_id,
                           n.canonical_point_id
                    FROM experiment_catalog_nodes n
                    WHERE n.node_kind = 'point'
                      AND n.status <> 'archived'
                      AND n.chapter_id = ANY(:chapter_ids)
                    ORDER BY n.chapter_id, n.display_order, n.title, n.id
                    """
                ),
                {"chapter_ids": sorted(SHOWCASE_CHAPTER_MASTERY_TARGETS)},
            )
            .mappings()
            .all()
        ]
        updated_by_chapter: dict[str, int] = {}
        for row in rows:
            chapter_id = str(row["chapter_id"])
            point_node_id = str(row["point_node_id"])
            score = showcase_mastery_score(chapter_id, point_node_id)
            evidence_count = showcase_evidence_count(chapter_id, point_node_id)
            updated_by_chapter[chapter_id] = updated_by_chapter.get(chapter_id, 0) + 1
            session.execute(
                text(
                    """
                    INSERT INTO student_point_mastery (
                      student_id, class_id, point_node_id, canonical_point_id,
                      mastery_prob, mastery_score, evidence_count,
                      last_evidence_kind, metadata, updated_at
                    )
                    VALUES (
                      :student_id, :class_id, :point_node_id, :canonical_point_id,
                      :mastery_prob, :mastery_score, :evidence_count,
                      :last_evidence_kind, CAST(:metadata AS jsonb), now()
                    )
                    ON CONFLICT (student_id, point_node_id)
                    DO UPDATE SET
                      class_id = EXCLUDED.class_id,
                      canonical_point_id = COALESCE(EXCLUDED.canonical_point_id, student_point_mastery.canonical_point_id),
                      mastery_prob = EXCLUDED.mastery_prob,
                      mastery_score = EXCLUDED.mastery_score,
                      evidence_count = EXCLUDED.evidence_count,
                      last_evidence_kind = EXCLUDED.last_evidence_kind,
                      metadata = EXCLUDED.metadata,
                      updated_at = now()
                    """
                ),
                {
                    "student_id": student.student_id,
                    "class_id": student.class_id,
                    "point_node_id": point_node_id,
                    "canonical_point_id": row.get("canonical_point_id"),
                    "mastery_prob": round(score / 100.0, 4),
                    "mastery_score": score,
                    "evidence_count": evidence_count,
                    "last_evidence_kind": "seed_showcase_assessment",
                    "metadata": _json_param(
                        {
                            "seed_owned": True,
                            "seed_source": SHOWCASE_MASTERY_PROFILE_SOURCE,
                            "student_id": student.student_id,
                            "chapter_id": chapter_id,
                            "chapter_target_score": SHOWCASE_CHAPTER_MASTERY_TARGETS[chapter_id],
                        }
                    ),
                },
            )
    return {
        "updated": True,
        "student_id": student.student_id,
        "source": SHOWCASE_MASTERY_PROFILE_SOURCE,
        "chapters": updated_by_chapter,
        "points": sum(updated_by_chapter.values()),
    }


def create_local_seed_report(user: Any, report: Any) -> Any:
    payload = _model_dump(report)
    wrong_answers = _as_dict_list(payload.get("wrong_answers"))
    report_type = str(payload.get("assessment_mode") or "smart")
    if report_type not in {"smart", "custom", "point"}:
        report_type = "smart"
    return _insert_report(
        student_id=_student_id(user),
        class_id=getattr(user, "class_id", None),
        report_type=report_type,
        source_session_id=str(report.session_id),
        source_table="student_smart_assessment_sessions",
        title=_report_title(report_type),
        score=float(report.score),
        correct_count=int(report.correct_count),
        total_count=int(report.total_count),
        correct_rate=float(report.correct_rate),
        wrong_count=len(wrong_answers),
        summary=_generated_text(_legacy_summary_text(payload), mode="seed_local_summary"),
        mistake_explanation=_generated_text(_legacy_mistake_text(wrong_answers), mode="seed_local_explanation"),
        prompt_snapshot={
            "source": "seed_local",
            "seed_source": SEED_SOURCE,
            "supported_inputs": ["score", "correct_count", "total_count", "experiments", "wrong_answers", "next_recommendation"],
        },
        payload=payload,
        completed_at=datetime.now(timezone.utc),
    )


async def simulate_student(student: DemoStudent) -> dict[str, Any]:
    user = _user_from_row(_load_user_row(student))
    response = start_student_smart_assessment(user)
    question_ids = [question.id for question in response.questions]
    questions = _questions_for_response(question_ids)
    answers = build_answers(student, questions)
    submitted = submit_student_smart_assessment(
        user,
        StudentSmartAssessmentSubmitRequest(session_id=response.session_id, answers=answers),
    )
    create_local_seed_report(user, submitted.report)
    mark_seed_metadata(student, response.session_id)
    return {
        "student_id": student.student_id,
        "class_id": student.class_id,
        "session_id": response.session_id,
        "questions": len(question_ids),
        "correct_count": submitted.report.correct_count,
        "total_count": submitted.report.total_count,
        "score": submitted.report.score,
    }


async def import_database(
    students: list[DemoStudent],
    *,
    replace: bool,
    reset_mastery: bool,
) -> dict[str, Any]:
    cleanup = cleanup_seed_generated_data(students, reset_mastery=reset_mastery) if replace else {}
    results: list[dict[str, Any]] = []
    for student in students:
        results.append(await simulate_student(student))
    showcase_profiles = [
        seed_showcase_mastery_profile(student)
        for student in students
        if student.student_id == SHOWCASE_STUDENT_ID
    ]
    scores = [float(item["score"]) for item in results]
    return {
        "ok": True,
        "seed_source": SEED_SOURCE,
        "cleanup": cleanup,
        "showcase_profiles": showcase_profiles,
        "summary": {
            "students": len(results),
            "min_score": round(min(scores), 2) if scores else None,
            "max_score": round(max(scores), 2) if scores else None,
            "average_score": round(sum(scores) / len(scores), 2) if scores else None,
        },
    }


def validate_database(students: list[DemoStudent]) -> dict[str, Any]:
    student_ids = _student_ids(students)
    expected = len(students)
    with db_session() as session:
        row = (
            session.execute(
                _expanded(
                    """
                    WITH seed_sessions AS (
                      SELECT id, student_id, status, total_count
                      FROM student_smart_assessment_sessions
                      WHERE student_id IN :student_ids
                        AND metadata->>'seed_source' = :seed_source
                    ),
                    seed_attempts AS (
                      SELECT DISTINCT student_id
                      FROM experiment_question_attempts
                      WHERE student_id IN :student_ids
                        AND metadata->>'seed_source' = :seed_source
                    ),
                    seed_reports AS (
                      SELECT DISTINCT student_id
                      FROM student_assessment_reports
                      WHERE student_id IN :student_ids
                        AND prompt_snapshot->>'seed_source' = :seed_source
                    )
                    SELECT
                      (SELECT count(DISTINCT student_id) FROM seed_sessions WHERE status = 'completed' AND total_count > 0) AS completed_students,
                      (SELECT count(*) FROM seed_sessions WHERE status = 'completed' AND total_count > 0) AS completed_sessions,
                      (SELECT count(DISTINCT student_id) FROM seed_attempts) AS attempted_students,
                      (SELECT count(DISTINCT student_id) FROM seed_reports) AS reported_students,
                      (SELECT count(*) FROM seed_sessions WHERE status = 'in_progress') AS open_sessions
                    """,
                    "student_ids",
                ),
                {"student_ids": student_ids, "seed_source": SEED_SOURCE},
            )
            .mappings()
            .one()
        )
    errors: list[str] = []
    for key in ("completed_students", "attempted_students", "reported_students"):
        if int(row[key] or 0) != expected:
            errors.append(f"{key}: expected {expected}, got {int(row[key] or 0)}")
    if int(row["open_sessions"] or 0) != 0:
        errors.append(f"open_sessions: expected 0, got {int(row['open_sessions'] or 0)}")
    return {
        "ok": not errors,
        "errors": errors,
        "seed_source": SEED_SOURCE,
        "summary": {
            "expected_students": expected,
            "completed_students": int(row["completed_students"] or 0),
            "completed_sessions": int(row["completed_sessions"] or 0),
            "attempted_students": int(row["attempted_students"] or 0),
            "reported_students": int(row["reported_students"] or 0),
            "open_sessions": int(row["open_sessions"] or 0),
        },
    }


def _select_students(students: list[DemoStudent], *, limit: int | None) -> list[DemoStudent]:
    if limit is None:
        return students
    if limit <= 0:
        raise ValueError("--limit must be greater than 0")
    return students[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed simulated smart-assessment answers for demo students.")
    parser.add_argument("command", choices=["import", "validate", "payload"], nargs="?", default="import")
    parser.add_argument("--seed-path", type=Path, default=DEFAULT_SEED_PATH)
    parser.add_argument("--skip-migrations", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--no-replace", action="store_true", help="Append data instead of replacing prior generated assessment seed data.")
    parser.add_argument("--keep-mastery", action="store_true", help="Do not reset derived mastery/progress rows for seed students before import.")
    args = parser.parse_args()

    payload = load_seed(args.seed_path)
    students = _select_students(seed_students(payload), limit=args.limit)
    if not args.limit and len(students) != EXPECTED_STUDENTS:
        raise SystemExit(f"Expected {EXPECTED_STUDENTS} demo students, got {len(students)}")

    if args.command == "payload":
        print(
            json.dumps(
                {
                    "ok": True,
                    "seed_source": SEED_SOURCE,
                    "summary": {
                        "students": len(students),
                        "classes": len({student.class_id for student in students}),
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if not args.skip_migrations:
        apply_migrations()

    if args.command == "validate":
        result = validate_database(students)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result["ok"]:
            raise SystemExit(1)
        return

    result = asyncio.run(
        import_database(
            students,
            replace=not args.no_replace,
            reset_mastery=not args.keep_mastery,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
