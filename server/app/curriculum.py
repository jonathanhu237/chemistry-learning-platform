from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import text

from server.app.database import db_session


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _version_payload(curriculum: dict[str, Any]) -> dict[str, Any]:
    return {
        "chapters": curriculum.get("chapters") or [],
        "knowledge_units": curriculum.get("knowledge_units") or [],
        "knowledge_points": curriculum.get("knowledge_points") or [],
    }


def load_curriculum_artifact(path: Path) -> dict[str, Any]:
    curriculum = json.loads(path.read_text(encoding="utf-8"))
    validation = curriculum.get("validation") or {}
    if not validation.get("ok"):
        raise ValueError("Curriculum artifact is not valid: " + "; ".join(validation.get("errors") or []))
    return curriculum


def create_curriculum_draft(curriculum: dict[str, Any], actor_user_id: str | None = None) -> dict[str, Any]:
    payload = _version_payload(curriculum)
    validation = curriculum.get("validation") or {}
    counts = validation.get("counts") or {
        "chapters": len(payload["chapters"]),
        "knowledge_units": len(payload["knowledge_units"]),
        "knowledge_points": len(payload["knowledge_points"]),
    }
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO curriculum_versions (
                      version_code, title, source_path, source_label, status,
                      imported_by, validation_report, counts, metadata
                    )
                    VALUES (
                      :version_code, :title, :source_path, :source_label, 'draft',
                      CAST(:imported_by AS uuid), CAST(:validation_report AS jsonb),
                      CAST(:counts AS jsonb), CAST(:metadata AS jsonb)
                    )
                    ON CONFLICT (version_code) DO UPDATE SET
                      title = EXCLUDED.title,
                      source_path = EXCLUDED.source_path,
                      source_label = EXCLUDED.source_label,
                      status = 'draft',
                      imported_by = EXCLUDED.imported_by,
                      validation_report = EXCLUDED.validation_report,
                      counts = EXCLUDED.counts,
                      metadata = EXCLUDED.metadata,
                      published_at = NULL,
                      archived_at = NULL,
                      updated_at = now()
                    RETURNING id, version_code, title, source_path, status, counts,
                              validation_report, created_at, updated_at
                    """
                ),
                {
                    "version_code": curriculum["version_code"],
                    "title": curriculum.get("title") or curriculum["version_code"],
                    "source_path": curriculum.get("source_path"),
                    "source_label": curriculum.get("source_label"),
                    "imported_by": actor_user_id,
                    "validation_report": _json(validation),
                    "counts": _json(counts),
                    "metadata": _json(payload),
                },
            )
            .mappings()
            .one()
        )
    return dict(row)


def list_curriculum_versions() -> list[dict[str, Any]]:
    with db_session() as session:
        rows = session.execute(
            text(
                """
                SELECT id, version_code, title, source_path, source_label, status,
                       counts, validation_report, published_at, archived_at,
                       created_at, updated_at
                FROM curriculum_versions
                ORDER BY created_at DESC
                """
            )
        ).mappings().all()
    return [dict(row) for row in rows]


def get_curriculum_version(version_id: str) -> dict[str, Any] | None:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT id, version_code, title, source_path, source_label, status,
                           counts, validation_report, metadata, published_at, archived_at,
                           created_at, updated_at
                    FROM curriculum_versions
                    WHERE id = CAST(:version_id AS uuid)
                    """
                ),
                {"version_id": version_id},
            )
            .mappings()
            .first()
        )
    return dict(row) if row else None


def publish_curriculum_version(version_id: str, actor_user_id: str | None = None) -> dict[str, Any]:
    with db_session() as session:
        version = (
            session.execute(
                text(
                    """
                    SELECT id, version_code, title, status, metadata, validation_report
                    FROM curriculum_versions
                    WHERE id = CAST(:version_id AS uuid)
                    FOR UPDATE
                    """
                ),
                {"version_id": version_id},
            )
            .mappings()
            .first()
        )
        if not version:
            raise ValueError("Curriculum version not found")
        if version["status"] == "archived":
            raise ValueError("Archived curriculum versions cannot be published")
        validation = version.get("validation_report") or {}
        if validation and not validation.get("ok", False):
            raise ValueError("Curriculum version validation failed")

        payload = version.get("metadata") or {}
        chapters = payload.get("chapters") or []
        units = payload.get("knowledge_units") or []
        points = payload.get("knowledge_points") or []
        if not chapters or not units or not points:
            raise ValueError("Curriculum version payload is incomplete")

        session.execute(
            text(
                """
                UPDATE curriculum_versions
                SET status = 'archived', archived_at = now(), updated_at = now()
                WHERE status = 'active' AND id <> CAST(:version_id AS uuid)
                """
            ),
            {"version_id": version_id},
        )

        for chapter in chapters:
            session.execute(
                text(
                    """
                    INSERT INTO chapters (
                      id, chapter_number, chapter_title, element_area, review_required,
                      curriculum_version_id, content_status, source_label, metadata,
                      published_at, updated_at
                    )
                    VALUES (
                      :id, :chapter_number, :chapter_title, :element_area, :review_required,
                      CAST(:version_id AS uuid), 'published', :source_label,
                      CAST(:metadata AS jsonb), now(), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      chapter_number = EXCLUDED.chapter_number,
                      chapter_title = EXCLUDED.chapter_title,
                      element_area = EXCLUDED.element_area,
                      review_required = EXCLUDED.review_required,
                      curriculum_version_id = EXCLUDED.curriculum_version_id,
                      content_status = 'published',
                      source_label = EXCLUDED.source_label,
                      metadata = EXCLUDED.metadata,
                      published_at = now(),
                      updated_at = now()
                    """
                ),
                {
                    "id": chapter["chapter_id"],
                    "chapter_number": chapter.get("chapter_number"),
                    "chapter_title": chapter.get("chapter_title"),
                    "element_area": chapter.get("element_area"),
                    "review_required": bool(chapter.get("review_required")),
                    "version_id": version_id,
                    "source_label": chapter.get("source_label"),
                    "metadata": _json({"source_file": chapter.get("source_file")}),
                },
            )

        for unit in units:
            session.execute(
                text(
                    """
                    INSERT INTO knowledge_units (
                      id, chapter_id, chapter_title, unit_index, unit_title,
                      review_required, curriculum_version_id, content_status,
                      source_label, metadata, published_at, updated_at
                    )
                    VALUES (
                      :id, :chapter_id, :chapter_title, :unit_index, :unit_title,
                      :review_required, CAST(:version_id AS uuid), 'published',
                      :source_label, CAST(:metadata AS jsonb), now(), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      chapter_id = EXCLUDED.chapter_id,
                      chapter_title = EXCLUDED.chapter_title,
                      unit_index = EXCLUDED.unit_index,
                      unit_title = EXCLUDED.unit_title,
                      review_required = EXCLUDED.review_required,
                      curriculum_version_id = EXCLUDED.curriculum_version_id,
                      content_status = 'published',
                      source_label = EXCLUDED.source_label,
                      metadata = EXCLUDED.metadata,
                      published_at = now(),
                      updated_at = now()
                    """
                ),
                {
                    "id": unit["unit_id"],
                    "chapter_id": unit.get("chapter_id"),
                    "chapter_title": unit.get("chapter_title"),
                    "unit_index": unit.get("unit_index"),
                    "unit_title": unit.get("unit_title"),
                    "review_required": bool(unit.get("review_required")),
                    "version_id": version_id,
                    "source_label": unit.get("source_label"),
                    "metadata": _json({"source_file": unit.get("source_file")}),
                },
            )

        for point in points:
            session.execute(
                text(
                    """
                    INSERT INTO knowledge_points (
                      id, chapter_id, chapter_title, unit_id, unit_title, content,
                      element_area, tags, difficulty, review_required,
                      curriculum_version_id, content_status, source_label, metadata,
                      published_at, updated_at
                    )
                    VALUES (
                      :id, :chapter_id, :chapter_title, :unit_id, :unit_title, :content,
                      :element_area, :tags, :difficulty, :review_required,
                      CAST(:version_id AS uuid), 'published', :source_label,
                      CAST(:metadata AS jsonb), now(), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      chapter_id = EXCLUDED.chapter_id,
                      chapter_title = EXCLUDED.chapter_title,
                      unit_id = EXCLUDED.unit_id,
                      unit_title = EXCLUDED.unit_title,
                      content = EXCLUDED.content,
                      element_area = EXCLUDED.element_area,
                      tags = EXCLUDED.tags,
                      difficulty = EXCLUDED.difficulty,
                      review_required = EXCLUDED.review_required,
                      curriculum_version_id = EXCLUDED.curriculum_version_id,
                      content_status = 'published',
                      source_label = EXCLUDED.source_label,
                      metadata = EXCLUDED.metadata,
                      published_at = now(),
                      updated_at = now()
                    """
                ),
                {
                    "id": point["knowledge_point_id"],
                    "chapter_id": point.get("chapter_id"),
                    "chapter_title": point.get("chapter_title"),
                    "unit_id": point.get("unit_id"),
                    "unit_title": point.get("unit_title"),
                    "content": point.get("content"),
                    "element_area": point.get("element_area"),
                    "tags": point.get("tags") or [],
                    "difficulty": point.get("difficulty"),
                    "review_required": bool(point.get("review_required")),
                    "version_id": version_id,
                    "source_label": point.get("source_label"),
                    "metadata": _json({"source_file": point.get("source_file")}),
                },
            )

        row = (
            session.execute(
                text(
                    """
                    UPDATE curriculum_versions
                    SET status = 'active',
                        published_at = now(),
                        archived_at = NULL,
                        updated_at = now(),
                        metadata = metadata || CAST(:publish_metadata AS jsonb)
                    WHERE id = CAST(:version_id AS uuid)
                    RETURNING id, version_code, title, status, counts, validation_report,
                              published_at, updated_at
                    """
                ),
                {
                    "version_id": version_id,
                    "publish_metadata": _json({"published_by": actor_user_id}),
                },
            )
            .mappings()
            .one()
        )
    return dict(row)


def archive_curriculum_version(version_id: str) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE curriculum_versions
                    SET status = 'archived', archived_at = now(), updated_at = now()
                    WHERE id = CAST(:version_id AS uuid)
                    RETURNING id, version_code, title, status, counts, validation_report,
                              archived_at, updated_at
                    """
                ),
                {"version_id": version_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise ValueError("Curriculum version not found")
    return dict(row)
