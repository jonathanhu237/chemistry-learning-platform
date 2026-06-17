from __future__ import annotations

import hashlib
import json
import mimetypes
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text

from server.app.config import get_settings
from server.app.schemas import FeedbackSubmitRequest, StudentEventRequest

FEEDBACK_TYPES = {"course_content", "experiment_resource", "ai_answer", "system_issue", "other"}
FEEDBACK_STATUSES = {"open", "in_progress", "resolved", "archived"}
ALLOWED_FEEDBACK_ATTACHMENT_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_FEEDBACK_ATTACHMENT_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}
FEEDBACK_ATTACHMENT_MAX_BYTES = 5 * 1024 * 1024

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
_memory_feedback_attachments: list[dict[str, Any]] = []


def _model_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model or {})


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
                WHERE CAST(:class_id AS text) IS NULL OR class_id = CAST(:class_id AS text)
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
    now = _utc_now()
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
        "attachment_count": 0,
        "attachments": [],
        "resolved_at": None,
        "created_at": now,
        "updated_at": now,
    }
    _memory_feedback_records.append(record)
    return dict(record)


def _normalize_attachment_mime(filename: str, content_type: str | None = None) -> str:
    guessed = content_type or mimetypes.guess_type(filename)[0] or ""
    normalized = guessed.split(";")[0].strip().lower()
    if normalized == "image/jpg":
        return "image/jpeg"
    return normalized


def _suffix_for_attachment(filename: str, mime_type: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix in ALLOWED_FEEDBACK_ATTACHMENT_SUFFIXES:
        return ".jpg" if suffix == ".jpeg" else suffix
    return {value: key for key, value in {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}.items()}.get(
        mime_type,
        "",
    )


def validate_feedback_attachment(filename: str, content: bytes, content_type: str | None = None) -> tuple[str, str]:
    mime_type = _normalize_attachment_mime(filename, content_type)
    suffix = _suffix_for_attachment(filename, mime_type)
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attachment file is empty")
    if len(content) > FEEDBACK_ATTACHMENT_MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Attachment file is too large")
    if suffix not in {".png", ".jpg", ".webp"} or mime_type not in ALLOWED_FEEDBACK_ATTACHMENT_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attachment must be a png, jpg, jpeg, or webp image")
    return mime_type, suffix


def _attachment_relative_path(feedback_id: str, attachment_id: str, suffix: str) -> str:
    safe_feedback_id = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(feedback_id))
    return (Path("feedback") / safe_feedback_id / f"{attachment_id}{suffix}").as_posix()


def _resolve_feedback_storage_path(relative_path: str) -> Path:
    root = get_settings().media_root.resolve()
    path = (root / relative_path).resolve()
    if not path.is_relative_to(root):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return path


def _attachment_to_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "feedback_id": str(row["feedback_id"]),
        "original_file_name": row.get("original_file_name"),
        "mime_type": row["mime_type"],
        "file_size_bytes": int(row.get("file_size_bytes") or 0),
        "created_at": row.get("created_at"),
    }


def list_feedback_attachments(session: Any, feedback_id: str) -> list[dict[str, Any]]:
    if get_settings().data_backend != "postgres":
        return [
            _attachment_to_item(row)
            for row in _memory_feedback_attachments
            if str(row.get("feedback_id")) == str(feedback_id)
        ]
    rows = (
        session.execute(
            text(
                """
                SELECT id, feedback_id, original_file_name, mime_type, file_size_bytes, created_at
                FROM feedback_attachments
                WHERE feedback_id = CAST(:feedback_id AS uuid)
                ORDER BY created_at, id
                """
            ),
            {"feedback_id": feedback_id},
        )
        .mappings()
        .all()
    )
    return [_attachment_to_item(dict(row)) for row in rows]


def create_feedback_attachment_record(
    feedback_id: str,
    *,
    filename: str,
    content: bytes,
    content_type: str | None = None,
    session: Any | None = None,
) -> dict[str, Any]:
    mime_type, suffix = validate_feedback_attachment(filename, content, content_type)
    attachment_id = str(uuid.uuid4())
    relative_path = _attachment_relative_path(feedback_id, attachment_id, suffix)
    absolute_path = _resolve_feedback_storage_path(relative_path)
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(content)
    checksum = hashlib.sha256(content).hexdigest()
    original_file_name = Path(filename or "feedback-image").name[:240] or "feedback-image"

    if get_settings().data_backend != "postgres":
        row = {
            "id": attachment_id,
            "feedback_id": feedback_id,
            "storage_path": relative_path,
            "original_file_name": original_file_name,
            "mime_type": mime_type,
            "file_size_bytes": len(content),
            "checksum_sha256": checksum,
            "created_at": _utc_now(),
        }
        _memory_feedback_attachments.append(row)
        for record in _memory_feedback_records:
            if str(record.get("id")) == str(feedback_id):
                record["attachment_count"] = int(record.get("attachment_count") or 0) + 1
                record["attachments"] = list_feedback_attachments(None, feedback_id)
                break
        return _attachment_to_item(row)

    if session is None:
        from server.app.database import db_session

        with db_session() as db:
            return create_feedback_attachment_record(
                feedback_id,
                filename=filename,
                content=content,
                content_type=content_type,
                session=db,
            )

    row = (
        session.execute(
            text(
                """
                INSERT INTO feedback_attachments (
                  id, feedback_id, storage_path, original_file_name, mime_type,
                  file_size_bytes, checksum_sha256
                )
                VALUES (
                  CAST(:id AS uuid), CAST(:feedback_id AS uuid), :storage_path,
                  :original_file_name, :mime_type, :file_size_bytes, :checksum_sha256
                )
                RETURNING id, feedback_id, original_file_name, mime_type, file_size_bytes, created_at
                """
            ),
            {
                "id": attachment_id,
                "feedback_id": feedback_id,
                "storage_path": relative_path,
                "original_file_name": original_file_name,
                "mime_type": mime_type,
                "file_size_bytes": len(content),
                "checksum_sha256": checksum,
            },
        )
        .mappings()
        .one()
    )
    return _attachment_to_item(dict(row))


def load_feedback_attachment_file(session: Any, feedback_id: str, attachment_id: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
                SELECT id, feedback_id, storage_path, original_file_name, mime_type, file_size_bytes, created_at
                FROM feedback_attachments
                WHERE id = CAST(:attachment_id AS uuid)
                  AND feedback_id = CAST(:feedback_id AS uuid)
                """
            ),
            {"feedback_id": feedback_id, "attachment_id": attachment_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    item = dict(row)
    path = _resolve_feedback_storage_path(item["storage_path"])
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file not found")
    item["absolute_path"] = path
    return item


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
    item["attachment_count"] = int(item.get("attachment_count") or 0)
    item["attachments"] = item.get("attachments") or []
    return item


def feedback_visibility_sql(user: Any, alias: str = "sf") -> tuple[str, dict[str, Any]]:
    return "TRUE", {}
