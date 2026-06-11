from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.database import apply_migrations, db_session

DEFAULT_SEED_PATH = ROOT / "data" / "seed" / "database_seed.json"
FORMAL_EXPERIMENTS_PATH = ROOT / "data" / "seed" / "formal_experiments.json"


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _list(value: Any) -> list[Any]:
    return list(value or [])


def _formal_experiment_ids() -> set[str]:
    if not FORMAL_EXPERIMENTS_PATH.exists():
        return set()
    data = json.loads(FORMAL_EXPERIMENTS_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return set()
    return {str(item.get("id")) for item in data.get("experiments") or [] if item.get("id")}


def _current_experiment_refs(values: Any, formal_ids: set[str]) -> list[str]:
    return [str(value) for value in values or [] if str(value) in formal_ids]


def _sanitize_seed(data: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    formal_ids = _formal_experiment_ids()
    sanitized = {key: [dict(row) for row in rows] for key, rows in data.items()}
    for row in sanitized.get("source_chunks", []):
        row["related_experiment_ids"] = _current_experiment_refs(row.get("related_experiment_ids"), formal_ids)
    for row in sanitized.get("questions", []):
        row["related_experiment_ids"] = _current_experiment_refs(row.get("related_experiment_ids"), formal_ids)
    sanitized["links"] = [
        row
        for row in sanitized.get("links", [])
        if not (
            (row.get("from_type") == "experiment" and row.get("from_id") not in formal_ids)
            or (row.get("to_type") == "experiment" and row.get("to_id") not in formal_ids)
        )
    ]
    sanitized["experiments"] = []
    sanitized["experiment_learning_cards"] = []
    return sanitized


def _content_status(review_required: bool | None) -> str:
    return "pending_review" if review_required else "published"


def _review_payload(row: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: row.get(key) for key in keys if key in row}


def _upsert_review_item(
    session: Any,
    *,
    target_type: str,
    target_id: str,
    title: str | None,
    chapter_id: str | None = None,
    knowledge_point_id: str | None = None,
    payload: dict[str, Any] | None = None,
    source_refs: list[dict[str, Any]] | None = None,
) -> None:
    session.execute(
        text(
            """
            INSERT INTO review_items (
              target_type, target_id, title, chapter_id, knowledge_point_id,
              status, risk_flags, payload, source_refs
            )
            VALUES (
              :target_type, :target_id, :title, :chapter_id, :knowledge_point_id,
              'pending_review', ARRAY['seed_import']::text[],
              CAST(:payload AS jsonb), CAST(:source_refs AS jsonb)
            )
            ON CONFLICT (target_type, target_id) DO UPDATE SET
              title = EXCLUDED.title,
              chapter_id = EXCLUDED.chapter_id,
              knowledge_point_id = EXCLUDED.knowledge_point_id,
              payload = EXCLUDED.payload,
              source_refs = EXCLUDED.source_refs,
              updated_at = now()
            """
        ),
        {
            "target_type": target_type,
            "target_id": target_id,
            "title": title,
            "chapter_id": chapter_id,
            "knowledge_point_id": knowledge_point_id,
            "payload": _json(payload or {}),
            "source_refs": _json(source_refs or []),
        },
    )


def load_seed(path: Path) -> dict[str, list[dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = [
        "source_documents",
        "chapters",
        "knowledge_units",
        "knowledge_points",
        "source_chunks",
        "experiments",
        "experiment_learning_cards",
        "questions",
        "links",
        "resources",
    ]
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"Seed file is missing keys: {', '.join(missing)}")
    return _sanitize_seed({key: list(data.get(key) or []) for key in required})


def validate_seed(data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    errors: list[str] = []
    chapter_ids = {row.get("chapter_id") for row in data["chapters"]}
    unit_ids = {row.get("unit_id") for row in data["knowledge_units"]}
    kp_ids = {row.get("knowledge_point_id") or row.get("id") for row in data["knowledge_points"]}
    document_ids = {row.get("document_id") for row in data["source_documents"]}
    chunk_ids = {row.get("chunk_id") or row.get("id") for row in data["source_chunks"]}
    experiment_ids = {row.get("experiment_id") or row.get("id") for row in data["experiments"]}

    for row in data["knowledge_units"]:
        if row.get("chapter_id") not in chapter_ids:
            errors.append(f"Unit {row.get('unit_id')} references missing chapter {row.get('chapter_id')}")
    for row in data["knowledge_points"]:
        if row.get("chapter_id") not in chapter_ids:
            errors.append(f"KP {row.get('id')} references missing chapter {row.get('chapter_id')}")
        if row.get("unit_id") not in unit_ids:
            errors.append(f"KP {row.get('id')} references missing unit {row.get('unit_id')}")
    for row in data["source_chunks"]:
        if row.get("document_id") not in document_ids:
            errors.append(f"Chunk {row.get('id')} references missing document {row.get('document_id')}")
    for row in data["questions"]:
        for kp_id in row.get("related_knowledge_point_ids") or []:
            if kp_id not in kp_ids:
                errors.append(f"Question {row.get('id')} references missing KP {kp_id}")
        for chunk_id in row.get("source_chunk_ids") or []:
            if chunk_id not in chunk_ids:
                errors.append(f"Question {row.get('id')} references missing chunk {chunk_id}")
    for row in data["experiment_learning_cards"]:
        if row.get("experiment_id") not in experiment_ids:
            errors.append(f"Learning card {row.get('id')} references missing experiment {row.get('experiment_id')}")

    return {
        "ok": not errors,
        "errors": errors,
        "counts": {key: len(value) for key, value in data.items()},
    }


def _delete_rows(session: Any, label: str, sql: str, params: dict[str, Any] | None = None) -> tuple[str, int]:
    result = session.execute(text(sql), params or {})
    rowcount = result.rowcount if result.rowcount is not None else 0
    return label, max(int(rowcount), 0)


def _sync_formal_experiment_compat_rows(session: Any) -> int:
    result = session.execute(
        text(
            """
            INSERT INTO experiments (
              id, name, element_area, element_group, objective, video_url, media_status,
              resource_mode, review_required, content_status, metadata, published_at, updated_at
            )
            SELECT
              fe.id,
              fe.title,
              NULL,
              (
                SELECT ecb.chapter_id
                FROM experiment_chapter_bindings ecb
                WHERE ecb.experiment_id = fe.id
                ORDER BY CASE ecb.coverage_type WHEN 'primary' THEN 0 WHEN 'partial' THEN 1 ELSE 2 END,
                         ecb.sort_order,
                         ecb.chapter_id
                LIMIT 1
              ),
              fe.summary,
              NULL,
              'pending',
              'formal_experiment_fk',
              false,
              fe.status,
              jsonb_build_object('formal_experiment_id', fe.id, 'formal_catalog', true),
              fe.published_at,
              now()
            FROM formal_experiments fe
            ON CONFLICT (id) DO UPDATE SET
              name = EXCLUDED.name,
              element_group = EXCLUDED.element_group,
              objective = EXCLUDED.objective,
              resource_mode = EXCLUDED.resource_mode,
              review_required = EXCLUDED.review_required,
              content_status = EXCLUDED.content_status,
              metadata = experiments.metadata || EXCLUDED.metadata,
              updated_at = now()
            """
        )
    )
    rowcount = result.rowcount if result.rowcount is not None else 0
    return max(int(rowcount), 0)


def replace_generated_seed_data(session: Any, data: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    chapter_ids = [row.get("chapter_id") or row.get("id") for row in data["chapters"]]
    cleanup_steps = [
        _delete_rows(
            session,
            "student_events",
            """
            DELETE FROM student_events se
            WHERE se.knowledge_point_id IS NOT NULL
               OR se.question_id IS NOT NULL
               OR (
                 se.experiment_id IS NOT NULL
                 AND NOT EXISTS (
                   SELECT 1 FROM formal_experiments fe WHERE fe.id = se.experiment_id
                 )
               )
            """,
        ),
        _delete_rows(session, "student_mastery", "DELETE FROM student_mastery"),
        _delete_rows(
            session,
            "media_bindings",
            """
            DELETE FROM media_bindings mb
            WHERE mb.target_type IN ('chapter', 'knowledge_unit', 'knowledge_point', 'learning_card')
               OR (
                 mb.target_type = 'experiment'
                 AND NOT EXISTS (
                   SELECT 1 FROM formal_experiments fe WHERE fe.id = mb.target_id
                 )
               )
            """,
        ),
        _delete_rows(
            session,
            "review_items",
            """
            DELETE FROM review_items ri
            WHERE ri.target_type IN ('source_chunk', 'learning_card', 'question', 'resource', 'link')
               OR (
                 ri.target_type = 'experiment'
                 AND NOT EXISTS (
                   SELECT 1 FROM formal_experiments fe WHERE fe.id = ri.target_id
                 )
               )
            """,
        ),
        _delete_rows(session, "links", "DELETE FROM links"),
        _delete_rows(session, "chunk_embeddings", "DELETE FROM chunk_embeddings"),
        _delete_rows(session, "experiment_learning_cards", "DELETE FROM experiment_learning_cards"),
        _delete_rows(session, "questions", "DELETE FROM questions"),
        _delete_rows(session, "resources", "DELETE FROM resources"),
        _delete_rows(session, "source_chunks", "DELETE FROM source_chunks"),
        _delete_rows(session, "source_documents", "DELETE FROM source_documents"),
        _delete_rows(
            session,
            "generated_experiments",
            """
            DELETE FROM experiments e
            WHERE NOT EXISTS (
              SELECT 1 FROM formal_experiments fe WHERE fe.id = e.id
            )
            """,
        ),
        _delete_rows(session, "knowledge_points", "DELETE FROM knowledge_points"),
        _delete_rows(session, "knowledge_units", "DELETE FROM knowledge_units"),
        _delete_rows(session, "curriculum_versions", "DELETE FROM curriculum_versions"),
        _delete_rows(
            session,
            "stale_chapters",
            "DELETE FROM chapters WHERE NOT (id = ANY(:chapter_ids))",
            {"chapter_ids": chapter_ids},
        ),
    ]
    return dict(cleanup_steps)


def import_seed(data: dict[str, list[dict[str, Any]]], *, replace_generated: bool = False) -> dict[str, Any]:
    report = validate_seed(data)
    if not report["ok"]:
        raise ValueError("Seed validation failed:\n" + "\n".join(report["errors"][:50]))

    with db_session() as session:
        if replace_generated:
            report["cleanup"] = replace_generated_seed_data(session, data)

        for row in data["source_documents"]:
            session.execute(
                text(
                    """
                    INSERT INTO source_documents (
                      id, file_name, path, archive_path, type, document_kind,
                      size_bytes, chapter_id, chapter_number, processing_status,
                      metadata, created_at, updated_at
                    )
                    VALUES (
                      :id, :file_name, :path, :archive_path, :type, :document_kind,
                      :size_bytes, :chapter_id, :chapter_number, :processing_status,
                      CAST(:metadata AS jsonb), COALESCE(CAST(:created_at AS timestamptz), now()),
                      COALESCE(CAST(:updated_at AS timestamptz), now())
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      file_name = EXCLUDED.file_name,
                      path = EXCLUDED.path,
                      archive_path = EXCLUDED.archive_path,
                      type = EXCLUDED.type,
                      document_kind = EXCLUDED.document_kind,
                      size_bytes = EXCLUDED.size_bytes,
                      chapter_id = EXCLUDED.chapter_id,
                      chapter_number = EXCLUDED.chapter_number,
                      processing_status = EXCLUDED.processing_status,
                      metadata = EXCLUDED.metadata,
                      updated_at = now()
                    """
                ),
                {
                    "id": row.get("document_id") or row.get("id"),
                    "file_name": row.get("file_name"),
                    "path": row.get("path"),
                    "archive_path": row.get("archive_path"),
                    "type": row.get("type"),
                    "document_kind": row.get("document_kind"),
                    "size_bytes": row.get("size_bytes"),
                    "chapter_id": row.get("chapter_id"),
                    "chapter_number": row.get("chapter_number"),
                    "processing_status": row.get("processing_status"),
                    "metadata": _json(row.get("metadata")),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at"),
                },
            )
            if row.get("review_required"):
                _upsert_review_item(
                    session,
                    target_type="source_chunk",
                    target_id=row.get("chunk_id") or row.get("id"),
                    title=(row.get("section_title") or row.get("text") or "")[:120],
                    chapter_id=row.get("chapter_id"),
                    payload=_review_payload(row, ["text", "page_number", "section_title", "document_id"]),
                    source_refs=[{"document_id": row.get("document_id"), "page_number": row.get("page_number")}],
                )

        for row in data["chapters"]:
            session.execute(
                text(
                    """
                    INSERT INTO chapters (
                      id, chapter_number, chapter_title, element_area, review_required,
                      source_label, metadata, content_status, published_at, created_at, updated_at
                    )
                    VALUES (
                      :id, :chapter_number, :chapter_title, :element_area, :review_required,
                      :source_label, CAST(:metadata AS jsonb), 'published', now(),
                      COALESCE(CAST(:created_at AS timestamptz), now()), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      chapter_number = EXCLUDED.chapter_number,
                      chapter_title = EXCLUDED.chapter_title,
                      element_area = EXCLUDED.element_area,
                      review_required = EXCLUDED.review_required,
                      source_label = EXCLUDED.source_label,
                      metadata = EXCLUDED.metadata,
                      content_status = EXCLUDED.content_status,
                      updated_at = now()
                    """
                ),
                {
                    "id": row.get("chapter_id") or row.get("id"),
                    "chapter_number": row.get("chapter_number"),
                    "chapter_title": row.get("chapter_title"),
                    "element_area": row.get("element_area"),
                    "review_required": bool(row.get("review_required")),
                    "source_label": row.get("source_label") or row.get("chapter_title"),
                    "metadata": _json({"source_file": row.get("source_file")}),
                    "created_at": row.get("created_at"),
                },
            )
            if row.get("review_required"):
                related_kps = row.get("related_knowledge_point_ids") or []
                _upsert_review_item(
                    session,
                    target_type="experiment",
                    target_id=row.get("experiment_id") or row.get("id"),
                    title=row.get("name"),
                    chapter_id=row.get("element_group"),
                    knowledge_point_id=related_kps[0] if related_kps else None,
                    payload=_review_payload(row, ["name", "objective", "phenomena", "equations", "explanation"]),
                    source_refs=[
                        {
                            "document_id": row.get("source_document_id"),
                            "pages": row.get("source_pages") or [],
                            "source_chunk_ids": row.get("source_chunk_ids") or [],
                        }
                    ],
                )

        for row in data["knowledge_units"]:
            session.execute(
                text(
                    """
                    INSERT INTO knowledge_units (
                      id, chapter_id, chapter_title, unit_index, unit_title, review_required,
                      source_label, metadata, content_status, published_at, created_at, updated_at
                    )
                    VALUES (
                      :id, :chapter_id, :chapter_title, :unit_index, :unit_title, :review_required,
                      :source_label, CAST(:metadata AS jsonb), 'published', now(),
                      COALESCE(CAST(:created_at AS timestamptz), now()), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      chapter_id = EXCLUDED.chapter_id,
                      chapter_title = EXCLUDED.chapter_title,
                      unit_index = EXCLUDED.unit_index,
                      unit_title = EXCLUDED.unit_title,
                      review_required = EXCLUDED.review_required,
                      source_label = EXCLUDED.source_label,
                      metadata = EXCLUDED.metadata,
                      content_status = EXCLUDED.content_status,
                      updated_at = now()
                    """
                ),
                {
                    "id": row.get("unit_id") or row.get("id"),
                    "chapter_id": row.get("chapter_id"),
                    "chapter_title": row.get("chapter_title"),
                    "unit_index": row.get("unit_index"),
                    "unit_title": row.get("unit_title"),
                    "review_required": bool(row.get("review_required")),
                    "source_label": row.get("source_label"),
                    "metadata": _json({"source_file": row.get("source_file")}),
                    "created_at": row.get("created_at"),
                },
            )
            if row.get("review_required"):
                related_kps = row.get("related_knowledge_points") or []
                _upsert_review_item(
                    session,
                    target_type="learning_card",
                    target_id=row.get("id"),
                    title=row.get("title"),
                    knowledge_point_id=related_kps[0] if related_kps else None,
                    payload=_review_payload(row, ["title", "objective", "phenomena", "equations", "principle", "safety_notes"]),
                    source_refs=[{"source_chunks": row.get("source_chunks") or []}],
                )

        for row in data["knowledge_points"]:
            session.execute(
                text(
                    """
                    INSERT INTO knowledge_points (
                      id, chapter_id, chapter_title, unit_id, unit_title, content,
                      element_area, tags, difficulty, review_required, source_label,
                      metadata, content_status, published_at, created_at, updated_at
                    )
                    VALUES (
                      :id, :chapter_id, :chapter_title, :unit_id, :unit_title, :content,
                      :element_area, :tags, :difficulty, :review_required, :source_label,
                      CAST(:metadata AS jsonb), 'published', now(),
                      COALESCE(CAST(:created_at AS timestamptz), now()), now()
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
                      source_label = EXCLUDED.source_label,
                      metadata = EXCLUDED.metadata,
                      content_status = EXCLUDED.content_status,
                      updated_at = now()
                    """
                ),
                {
                    "id": row.get("knowledge_point_id") or row.get("id"),
                    "chapter_id": row.get("chapter_id"),
                    "chapter_title": row.get("chapter_title"),
                    "unit_id": row.get("unit_id"),
                    "unit_title": row.get("unit_title"),
                    "content": row.get("content"),
                    "element_area": row.get("element_area"),
                    "tags": _list(row.get("tags")),
                    "difficulty": row.get("difficulty"),
                    "review_required": bool(row.get("review_required")),
                    "source_label": row.get("source_label"),
                    "metadata": _json({"source_file": row.get("source_file")}),
                    "created_at": row.get("created_at"),
                },
            )
            if row.get("review_required"):
                related_kps = row.get("related_knowledge_point_ids") or []
                first_kp = related_kps[0] if related_kps else None
                first_point = next(
                    (point for point in data["knowledge_points"] if (point.get("knowledge_point_id") or point.get("id")) == first_kp),
                    {},
                )
                _upsert_review_item(
                    session,
                    target_type="question",
                    target_id=row.get("question_id") or row.get("id"),
                    title=(row.get("stem") or "")[:120],
                    chapter_id=first_point.get("chapter_id"),
                    knowledge_point_id=first_kp,
                    payload=_review_payload(row, ["question_type", "stem", "options", "answer", "explanation", "difficulty"]),
                    source_refs=[{"source_chunk_ids": row.get("source_chunk_ids") or []}],
                )

        for row in data["source_chunks"]:
            metadata = dict(row.get("metadata") or {})
            for key in ("source_file", "source_path", "document_kind", "candidate_knowledge_point_ids"):
                if key in row:
                    metadata[key] = row.get(key)
            session.execute(
                text(
                    """
                    INSERT INTO source_chunks (
                      id, document_id, chapter_id, page_number, section_title, chunk_index,
                      text, markdown, related_knowledge_point_ids, related_experiment_ids,
                      tags, metadata, review_required, content_status, created_at, updated_at
                    )
                    VALUES (
                      :id, :document_id, :chapter_id, :page_number, :section_title, :chunk_index,
                      :text, :markdown, :related_knowledge_point_ids, :related_experiment_ids,
                      :tags, CAST(:metadata AS jsonb), :review_required, :content_status,
                      COALESCE(CAST(:created_at AS timestamptz), now()), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      document_id = EXCLUDED.document_id,
                      chapter_id = EXCLUDED.chapter_id,
                      page_number = EXCLUDED.page_number,
                      section_title = EXCLUDED.section_title,
                      chunk_index = EXCLUDED.chunk_index,
                      text = EXCLUDED.text,
                      markdown = EXCLUDED.markdown,
                      related_knowledge_point_ids = EXCLUDED.related_knowledge_point_ids,
                      related_experiment_ids = EXCLUDED.related_experiment_ids,
                      tags = EXCLUDED.tags,
                      metadata = EXCLUDED.metadata,
                      review_required = EXCLUDED.review_required,
                      content_status = EXCLUDED.content_status,
                      updated_at = now()
                    """
                ),
                {
                    "id": row.get("chunk_id") or row.get("id"),
                    "document_id": row.get("document_id"),
                    "chapter_id": row.get("chapter_id"),
                    "page_number": row.get("page_number"),
                    "section_title": row.get("section_title"),
                    "chunk_index": row.get("chunk_index"),
                    "text": row.get("text"),
                    "markdown": row.get("markdown"),
                    "related_knowledge_point_ids": _list(row.get("related_knowledge_point_ids") or row.get("candidate_knowledge_point_ids")),
                    "related_experiment_ids": _list(row.get("related_experiment_ids")),
                    "tags": _list(row.get("tags")),
                    "metadata": _json(metadata),
                    "review_required": bool(row.get("review_required")),
                    "content_status": _content_status(bool(row.get("review_required"))),
                    "created_at": row.get("created_at"),
                },
            )

        for row in data["experiments"]:
            metadata = {
                "source_file": row.get("source_file"),
                "source_document_id": row.get("source_document_id"),
                "source_pages": row.get("source_pages"),
                "source_text_preview": row.get("source_text_preview"),
                "related_knowledge_point_ids": row.get("related_knowledge_point_ids") or [],
                "source_chunk_ids": row.get("source_chunk_ids") or [],
            }
            session.execute(
                text(
                    """
                    INSERT INTO experiments (
                      id, name, element_area, element_group, related_elements, objective,
                      reagents, steps, phenomena, equations, explanation, video_url,
                      media_status, resource_mode, review_required, content_status,
                      metadata, created_at, updated_at
                    )
                    VALUES (
                      :id, :name, :element_area, :element_group, :related_elements, :objective,
                      :reagents, CAST(:steps AS jsonb), CAST(:phenomena AS jsonb),
                      CAST(:equations AS jsonb), :explanation, :video_url, :media_status,
                      :resource_mode, :review_required, :content_status, CAST(:metadata AS jsonb),
                      COALESCE(CAST(:created_at AS timestamptz), now()), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      name = EXCLUDED.name,
                      element_area = EXCLUDED.element_area,
                      element_group = EXCLUDED.element_group,
                      related_elements = EXCLUDED.related_elements,
                      objective = EXCLUDED.objective,
                      reagents = EXCLUDED.reagents,
                      steps = EXCLUDED.steps,
                      phenomena = EXCLUDED.phenomena,
                      equations = EXCLUDED.equations,
                      explanation = EXCLUDED.explanation,
                      video_url = EXCLUDED.video_url,
                      media_status = EXCLUDED.media_status,
                      resource_mode = EXCLUDED.resource_mode,
                      review_required = EXCLUDED.review_required,
                      content_status = EXCLUDED.content_status,
                      metadata = EXCLUDED.metadata,
                      updated_at = now()
                    """
                ),
                {
                    "id": row.get("experiment_id") or row.get("id"),
                    "name": row.get("name"),
                    "element_area": row.get("element_area"),
                    "element_group": row.get("element_group"),
                    "related_elements": _list(row.get("related_elements")),
                    "objective": row.get("objective"),
                    "reagents": _list(row.get("reagents")),
                    "steps": _json(row.get("steps") or []),
                    "phenomena": _json(row.get("phenomena") or []),
                    "equations": _json(row.get("equations") or []),
                    "explanation": row.get("explanation"),
                    "video_url": row.get("video_url"),
                    "media_status": row.get("media_status") or "pending",
                    "resource_mode": row.get("resource_mode") or "text_card",
                    "review_required": bool(row.get("review_required")),
                    "content_status": _content_status(bool(row.get("review_required"))),
                    "metadata": _json(metadata),
                    "created_at": row.get("created_at"),
                },
            )

        for row in data["experiment_learning_cards"]:
            session.execute(
                text(
                    """
                    INSERT INTO experiment_learning_cards (
                      id, experiment_id, title, objective, reagents, steps, phenomena,
                      equations, principle, safety_notes, related_knowledge_points,
                      source_chunks, review_required, content_status, metadata, created_at, updated_at
                    )
                    VALUES (
                      :id, :experiment_id, :title, :objective, :reagents, CAST(:steps AS jsonb),
                      CAST(:phenomena AS jsonb), CAST(:equations AS jsonb), :principle,
                      :safety_notes, :related_knowledge_points, :source_chunks,
                      :review_required, :content_status, CAST(:metadata AS jsonb),
                      COALESCE(CAST(:created_at AS timestamptz), now()), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      experiment_id = EXCLUDED.experiment_id,
                      title = EXCLUDED.title,
                      objective = EXCLUDED.objective,
                      reagents = EXCLUDED.reagents,
                      steps = EXCLUDED.steps,
                      phenomena = EXCLUDED.phenomena,
                      equations = EXCLUDED.equations,
                      principle = EXCLUDED.principle,
                      safety_notes = EXCLUDED.safety_notes,
                      related_knowledge_points = EXCLUDED.related_knowledge_points,
                      source_chunks = EXCLUDED.source_chunks,
                      review_required = EXCLUDED.review_required,
                      content_status = EXCLUDED.content_status,
                      metadata = EXCLUDED.metadata,
                      updated_at = now()
                    """
                ),
                {
                    "id": row.get("id"),
                    "experiment_id": row.get("experiment_id"),
                    "title": row.get("title"),
                    "objective": row.get("objective"),
                    "reagents": _list(row.get("reagents")),
                    "steps": _json(row.get("steps") or []),
                    "phenomena": _json(row.get("phenomena") or []),
                    "equations": _json(row.get("equations") or []),
                    "principle": row.get("principle"),
                    "safety_notes": _list(row.get("safety_notes")),
                    "related_knowledge_points": _list(row.get("related_knowledge_points")),
                    "source_chunks": _list(row.get("source_chunks")),
                    "review_required": bool(row.get("review_required")),
                    "content_status": _content_status(bool(row.get("review_required"))),
                    "metadata": _json({"source_file": row.get("source_file")}),
                    "created_at": row.get("created_at"),
                },
            )

        for row in data["questions"]:
            session.execute(
                text(
                    """
                    INSERT INTO questions (
                      id, question_type, stem, options, answer, explanation, difficulty,
                      related_knowledge_point_ids, related_experiment_ids, source_chunk_ids,
                      review_required, content_status, metadata, created_at, updated_at
                    )
                    VALUES (
                      :id, :question_type, :stem, CAST(:options AS jsonb), :answer, :explanation,
                      :difficulty, :related_knowledge_point_ids, :related_experiment_ids,
                      :source_chunk_ids, :review_required, :content_status, CAST(:metadata AS jsonb),
                      COALESCE(CAST(:created_at AS timestamptz), now()), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      question_type = EXCLUDED.question_type,
                      stem = EXCLUDED.stem,
                      options = EXCLUDED.options,
                      answer = EXCLUDED.answer,
                      explanation = EXCLUDED.explanation,
                      difficulty = EXCLUDED.difficulty,
                      related_knowledge_point_ids = EXCLUDED.related_knowledge_point_ids,
                      related_experiment_ids = EXCLUDED.related_experiment_ids,
                      source_chunk_ids = EXCLUDED.source_chunk_ids,
                      review_required = EXCLUDED.review_required,
                      content_status = EXCLUDED.content_status,
                      metadata = EXCLUDED.metadata,
                      updated_at = now()
                    """
                ),
                {
                    "id": row.get("question_id") or row.get("id"),
                    "question_type": row.get("question_type"),
                    "stem": row.get("stem"),
                    "options": _json(row.get("options") or []),
                    "answer": row.get("answer"),
                    "explanation": row.get("explanation"),
                    "difficulty": row.get("difficulty"),
                    "related_knowledge_point_ids": _list(row.get("related_knowledge_point_ids")),
                    "related_experiment_ids": _list(row.get("related_experiment_ids")),
                    "source_chunk_ids": _list(row.get("source_chunk_ids")),
                    "review_required": bool(row.get("review_required")),
                    "content_status": _content_status(bool(row.get("review_required"))),
                    "metadata": _json({"source_file": row.get("source_file")}),
                    "created_at": row.get("created_at"),
                },
            )

        for row in data["resources"]:
            session.execute(
                text(
                    """
                    INSERT INTO resources (
                      id, document_id, title, resource_type, path, metadata,
                      review_required, content_status, created_at, updated_at
                    )
                    VALUES (
                      :id, :document_id, :title, :resource_type, :path, CAST(:metadata AS jsonb),
                      :review_required, :content_status,
                      COALESCE(CAST(:created_at AS timestamptz), now()), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      document_id = EXCLUDED.document_id,
                      title = EXCLUDED.title,
                      resource_type = EXCLUDED.resource_type,
                      path = EXCLUDED.path,
                      metadata = EXCLUDED.metadata,
                      review_required = EXCLUDED.review_required,
                      content_status = EXCLUDED.content_status,
                      updated_at = now()
                    """
                ),
                {
                    "id": row.get("resource_id") or row.get("id"),
                    "document_id": row.get("document_id"),
                    "title": row.get("title"),
                    "resource_type": row.get("resource_type"),
                    "path": row.get("path"),
                    "metadata": _json(row.get("metadata")),
                    "review_required": bool(row.get("review_required")),
                    "content_status": _content_status(bool(row.get("review_required"))),
                    "created_at": row.get("created_at"),
                },
            )
            if row.get("review_required"):
                _upsert_review_item(
                    session,
                    target_type="resource",
                    target_id=row.get("resource_id") or row.get("id"),
                    title=row.get("title"),
                    payload=_review_payload(row, ["title", "resource_type", "path", "metadata"]),
                    source_refs=[{"document_id": row.get("document_id")}],
                )

        for row in data["links"]:
            link_id = session.execute(
                text(
                    """
                    INSERT INTO links (
                      from_type, from_id, relation, to_type, to_id, confidence,
                      review_required, content_status, created_at, updated_at
                    )
                    VALUES (
                      :from_type, :from_id, :relation, :to_type, :to_id, :confidence,
                      :review_required, :content_status,
                      COALESCE(CAST(:created_at AS timestamptz), now()), now()
                    )
                    ON CONFLICT (from_type, from_id, relation, to_type, to_id) DO UPDATE SET
                      confidence = EXCLUDED.confidence,
                      review_required = EXCLUDED.review_required,
                      content_status = EXCLUDED.content_status,
                      updated_at = now()
                    RETURNING id
                    """
                ),
                {
                    "from_type": row.get("from_type"),
                    "from_id": row.get("from_id"),
                    "relation": row.get("relation"),
                    "to_type": row.get("to_type"),
                    "to_id": row.get("to_id"),
                    "confidence": row.get("confidence"),
                    "review_required": bool(row.get("review_required")),
                    "content_status": _content_status(bool(row.get("review_required"))),
                    "created_at": row.get("created_at"),
                },
            ).scalar_one()
            if row.get("review_required"):
                _upsert_review_item(
                    session,
                    target_type="link",
                    target_id=str(link_id),
                    title=f"{row.get('from_type')} {row.get('from_id')} -> {row.get('to_type')} {row.get('to_id')}",
                    knowledge_point_id=row.get("to_id") if row.get("to_type") == "knowledge_point" else None,
                    payload=_review_payload(row, ["from_type", "from_id", "relation", "to_type", "to_id", "confidence"]),
                    source_refs=[{"from_id": row.get("from_id"), "to_id": row.get("to_id")}],
                )

        report["formal_experiment_compat_rows"] = _sync_formal_experiment_compat_rows(session)

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Import generated seed data into Postgres.")
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED_PATH)
    parser.add_argument("--skip-migrations", action="store_true")
    parser.add_argument(
        "--replace-generated",
        action="store_true",
        help="Delete generated curriculum/corpus seed rows before importing, while preserving formal admin data.",
    )
    args = parser.parse_args()

    if not args.skip_migrations:
        applied = apply_migrations()
        if applied:
            print("Applied migrations: " + ", ".join(applied))

    data = load_seed(args.seed)
    report = import_seed(data, replace_generated=args.replace_generated)
    if report.get("cleanup"):
        print("Replaced generated seed data:")
        for key, count in report["cleanup"].items():
            print(f"- {key}: {count}")
    print("Imported seed data:")
    for key, count in report["counts"].items():
        print(f"- {key}: {count}")
    print(f"- formal_experiment_compat_rows: {report.get('formal_experiment_compat_rows', 0)}")


if __name__ == "__main__":
    main()
