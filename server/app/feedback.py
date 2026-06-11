from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text

from server.app.config import get_settings
from server.app.schemas import FeedbackSubmitRequest, StudentEventRequest

FEEDBACK_TYPES = {"course_content", "experiment_resource", "ai_answer", "system_issue", "other"}
FEEDBACK_STATUSES = {"open", "in_progress", "resolved", "archived"}

FEEDBACK_TYPE_ALIASES = {
    "course": "course_content",
    "content": "course_content",
    "course_content": "course_content",
    "experiment": "experiment_resource",
    "experiment_resource": "experiment_resource",
    "resource": "experiment_resource",
    "video": "experiment_resource",
    "ai": "ai_answer",
    "ai_answer": "ai_answer",
    "agent": "ai_answer",
    "program": "system_issue",
    "system": "system_issue",
    "system_issue": "system_issue",
    "bug": "system_issue",
    "other": "other",
}

_memory_feedback_records: list[dict[str, Any]] = []


def _model_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model or {})


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _clean_optional(value: Any) -> str | None:
    text_value = str(value or "").strip()
    return text_value or None


def normalize_feedback_type(value: Any) -> str:
    key = str(value or "other").strip().lower()
    return FEEDBACK_TYPE_ALIASES.get(key, "other")


def feedback_submit_from_event(payload: StudentEventRequest) -> FeedbackSubmitRequest:
    data = _model_dump(payload)
    metadata = dict(data.get("metadata") or {})
    content = _clean_optional(
        metadata.get("content")
        or metadata.get("feedback_content")
        or metadata.get("message")
        or metadata.get("feedback")
    )
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feedback content is required")
    return FeedbackSubmitRequest(
        student_id=data["student_id"],
        feedback_type=normalize_feedback_type(metadata.get("feedback_type") or metadata.get("type")),
        content=content,
        class_id=_clean_optional(metadata.get("class_id")),
        chapter_id=_clean_optional(data.get("chapter_id")),
        unit_id=_clean_optional(data.get("unit_id")),
        knowledge_point_id=_clean_optional(data.get("knowledge_point_id")),
        experiment_id=_clean_optional(data.get("experiment_id")),
        page_path=_clean_optional(metadata.get("page_path") or metadata.get("page")),
        metadata=metadata,
    )


def _load_student_snapshot(session: Any, student_id: str, class_id: str | None = None) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
                SELECT student_id, student_name, class_id, class_name
                FROM (
                  SELECT sp.student_id, sp.student_name, sp.class_id, c.class_name, 1 AS source_rank
                  FROM student_profiles sp
                  LEFT JOIN classes c ON c.id = sp.class_id
                  WHERE sp.student_id = :student_id
                  UNION ALL
                  SELECT re.student_id, re.student_name, re.class_id, c.class_name, 2 AS source_rank
                  FROM roster_entries re
                  LEFT JOIN classes c ON c.id = re.class_id
                  WHERE re.student_id = :student_id
                  UNION ALL
                  SELECT COALESCE(s.student_id, s.id) AS student_id,
                         s.display_name AS student_name,
                         s.class_id,
                         COALESCE(c.class_name, s.class_name) AS class_name,
                         3 AS source_rank
                  FROM students s
                  LEFT JOIN classes c ON c.id = s.class_id
                  WHERE s.id = :student_id OR s.student_id = :student_id
                ) candidates
                WHERE :class_id IS NULL OR class_id = :class_id
                ORDER BY source_rank, class_id NULLS LAST
                LIMIT 1
                """
            ),
            {"student_id": student_id, "class_id": class_id},
        )
        .mappings()
        .first()
    )
    if row:
        return dict(row)
    if class_id:
        class_row = session.execute(text("SELECT class_name FROM classes WHERE id = :class_id"), {"class_id": class_id}).mappings().first()
        if not class_row:
            return {"student_id": student_id, "student_name": None, "class_id": None, "class_name": None}
        return {
            "student_id": student_id,
            "student_name": None,
            "class_id": class_id,
            "class_name": class_row["class_name"],
        }
    return {"student_id": student_id, "student_name": None, "class_id": None, "class_name": None}


def _memory_feedback_record(payload: FeedbackSubmitRequest, source_event_id: int | None = None) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    data = _model_dump(payload)
    record = {
        "id": f"memory-{uuid.uuid4().hex}",
        "student_id": data["student_id"],
        "class_id": data.get("class_id"),
        "student_name_snapshot": None,
        "class_name_snapshot": None,
        "feedback_type": normalize_feedback_type(data.get("feedback_type")),
        "content": data["content"],
        "status": "open",
        "chapter_id": data.get("chapter_id"),
        "unit_id": data.get("unit_id"),
        "knowledge_point_id": data.get("knowledge_point_id"),
        "experiment_id": data.get("experiment_id"),
        "page_path": data.get("page_path"),
        "source_event_id": source_event_id,
        "handler_user_id": None,
        "handler_display_name": None,
        "internal_note": None,
        "metadata": data.get("metadata") or {},
        "resolved_at": None,
        "created_at": now,
        "updated_at": now,
    }
    _memory_feedback_records.append(record)
    return dict(record)


def create_feedback_record(
    payload: FeedbackSubmitRequest,
    *,
    session: Any | None = None,
    source_event_id: int | None = None,
) -> dict[str, Any]:
    if get_settings().data_backend != "postgres":
        return _memory_feedback_record(payload, source_event_id=source_event_id)
    if session is None:
        from server.app.database import db_session

        with db_session() as db:
            return create_feedback_record(payload, session=db, source_event_id=source_event_id)

    data = _model_dump(payload)
    student_id = str(data["student_id"]).strip()
    class_id = _clean_optional(data.get("class_id"))
    snapshot = _load_student_snapshot(session, student_id, class_id)
    effective_class_id = class_id or snapshot.get("class_id")
    row = (
        session.execute(
            text(
                """
                INSERT INTO student_feedback (
                  student_id, class_id, student_name_snapshot, class_name_snapshot,
                  feedback_type, content, status, chapter_id, unit_id, knowledge_point_id,
                  experiment_id, page_path, source_event_id, metadata, updated_at
                )
                VALUES (
                  :student_id, :class_id, :student_name_snapshot, :class_name_snapshot,
                  :feedback_type, :content, 'open', :chapter_id, :unit_id, :knowledge_point_id,
                  :experiment_id, :page_path, :source_event_id, CAST(:metadata AS jsonb), now()
                )
                RETURNING *
                """
            ),
            {
                "student_id": student_id,
                "class_id": effective_class_id,
                "student_name_snapshot": snapshot.get("student_name"),
                "class_name_snapshot": snapshot.get("class_name"),
                "feedback_type": normalize_feedback_type(data.get("feedback_type")),
                "content": str(data["content"]).strip(),
                "chapter_id": _clean_optional(data.get("chapter_id")),
                "unit_id": _clean_optional(data.get("unit_id")),
                "knowledge_point_id": _clean_optional(data.get("knowledge_point_id")),
                "experiment_id": _clean_optional(data.get("experiment_id")),
                "page_path": _clean_optional(data.get("page_path")),
                "source_event_id": source_event_id,
                "metadata": _json(data.get("metadata") or {}),
            },
        )
        .mappings()
        .one()
    )
    return feedback_row_to_item(dict(row))


def feedback_row_to_item(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    item["id"] = str(item["id"])
    if item.get("handler_user_id") is not None:
        item["handler_user_id"] = str(item["handler_user_id"])
    item["metadata"] = item.get("metadata") or {}
    return item


def feedback_visibility_sql(user: Any, alias: str = "sf") -> tuple[str, dict[str, Any]]:
    return "TRUE", {}
