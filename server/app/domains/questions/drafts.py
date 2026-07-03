from __future__ import annotations

from typing import Any

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from sqlalchemy import text

from server.app.infrastructure.database import db_session
from server.app.experiment_teacher_schemas import DraftUpdateRequest
from server.app.domains.questions.bank import (
    _insert_question,
    _json,
    _json_array,
    _validate_question_payload,
    normalize_question_point_identity,
)
from server.app.domains.questions.duplicate_risk import attach_duplicate_risk_for_payload
from server.app.domains.questions.generation import question_payload_has_catalog_evidence_lineage


def list_question_drafts(
    *,
    generation_id: str | None = None,
    experiment_id: str | None = None,
    point_node_id: str | None = None,
    canonical_point_id: str | None = None,
) -> dict[str, Any]:
    filters = ["d.status = 'draft'"]
    params: dict[str, Any] = {}
    if generation_id:
        filters.append("d.generation_id = CAST(:generation_id AS uuid)")
        params["generation_id"] = generation_id
    if experiment_id:
        filters.append("d.experiment_id = :experiment_id")
        params["experiment_id"] = experiment_id
    if point_node_id:
        filters.append(
            """
            EXISTS (
              SELECT 1
              FROM jsonb_array_elements_text(
                COALESCE(
                  d.payload->'source_placement_node_ids',
                  d.payload->'primary_point_node_ids',
                  d.payload->'metadata'->'source_placement_node_ids',
                  d.payload->'metadata'->'primary_point_node_ids',
                  '[]'::jsonb
                )
              ) AS point_ids(value)
              WHERE point_ids.value = :point_node_id
            )
            """
        )
        params["point_node_id"] = point_node_id
    if canonical_point_id:
        filters.append(
            """
            EXISTS (
              SELECT 1
              FROM jsonb_array_elements_text(
                COALESCE(
                  d.payload->'primary_canonical_point_ids',
                  d.payload->'metadata'->'primary_canonical_point_ids',
                  '[]'::jsonb
                )
              ) AS canonical_ids(value)
              WHERE canonical_ids.value = :canonical_point_id
            )
            """
        )
        params["canonical_point_id"] = canonical_point_id
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    f"""
                    SELECT d.*, g.prompt, g.mode, g.warning, fe.code AS experiment_code, fe.title AS experiment_title
                    FROM experiment_question_drafts d
                    JOIN experiment_question_generations g ON g.id = d.generation_id
                    JOIN formal_experiments fe ON fe.id = d.experiment_id
                    WHERE {" AND ".join(filters)}
                    ORDER BY d.created_at DESC
                    """
                ),
                params,
            )
            .mappings()
            .all()
        ]
    return {"items": rows, "total": len(rows)}


def update_question_draft(
    *,
    payload: DraftUpdateRequest,
    draft_id: str,
) -> dict[str, Any]:
    normalized, errors = _validate_question_payload({**payload.payload, "status": "draft"})
    draft_payload = normalized or {**payload.payload, "status": "draft"}
    with db_session() as session:
        draft_payload = attach_duplicate_risk_for_payload(
            session,
            payload=draft_payload,
            owner_kind="draft",
            owner_id=draft_id,
        )
        row = (
            session.execute(
                text(
                    """
                    UPDATE experiment_question_drafts
                    SET payload = CAST(:payload AS jsonb),
                        validation_errors = CAST(:errors AS jsonb),
                        status = COALESCE(:status, status),
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    RETURNING *
                    """
                ),
                {
                    "id": draft_id,
                    "payload": _json(draft_payload),
                    "errors": _json_array(errors),
                    "status": payload.status,
                },
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return dict(row)


def publish_question_draft(
    *,
    draft_id: str,
    user: Any,
) -> dict[str, Any]:
    with db_session() as session:
        draft = (
            session.execute(text("SELECT * FROM experiment_question_drafts WHERE id = CAST(:id AS uuid)"), {"id": draft_id})
            .mappings()
            .first()
        )
        if not draft:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
        if draft["status"] != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft questions can be published")
        payload = dict(draft["payload"] or {})
        payload = attach_duplicate_risk_for_payload(
            session,
            payload=payload,
            owner_kind="draft",
            owner_id=draft_id,
        )
        metadata = dict(payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {})
        revoked_from_question_id = str(metadata.get("revoked_from_question_id") or "").strip()
        if not revoked_from_question_id and not question_payload_has_catalog_evidence_lineage(payload):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": ["catalog-node evidence lineage is required before publication"]},
            )
        payload["status"] = "published"
        if revoked_from_question_id:
            normalized, errors = _validate_question_payload(payload)
            if errors or normalized is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"errors": errors})
            normalized = normalize_question_point_identity(session, normalized)
            row = (
                session.execute(
                    text(
                        """
                        UPDATE experiment_questions
                        SET generation_id = CAST(:generation_id AS uuid),
                            question_type = :question_type,
                            stem = :stem,
                            options = CAST(:options AS jsonb),
                            answer = CAST(:answer AS jsonb),
                            explanation = :explanation,
                            difficulty = :difficulty,
                            related_chapter_ids = :related_chapter_ids,
                            related_knowledge_point_ids = :related_knowledge_point_ids,
                            source_chunk_ids = :source_chunk_ids,
                            source_refs = CAST(:source_refs AS jsonb),
                            primary_point_node_ids = :primary_point_node_ids,
                            primary_canonical_point_ids = :primary_canonical_point_ids,
                            source_placement_node_ids = :source_placement_node_ids,
                            metadata = CAST(:metadata AS jsonb),
                            status = 'published',
                            published_by = CAST(:actor AS uuid),
                            published_at = now(),
                            updated_at = now()
                        WHERE id = CAST(:id AS uuid)
                        RETURNING *
                        """
                    ),
                    {
                        "id": revoked_from_question_id,
                        "generation_id": str(draft["generation_id"]),
                        "question_type": normalized["question_type"],
                        "stem": normalized["stem"],
                        "options": _json_array(normalized["options"]),
                        "answer": _json(normalized["answer"]),
                        "explanation": normalized["explanation"],
                        "difficulty": normalized["difficulty"],
                        "related_chapter_ids": normalized["related_chapter_ids"],
                        "related_knowledge_point_ids": normalized["related_knowledge_point_ids"],
                        "source_chunk_ids": normalized["source_chunk_ids"],
                        "source_refs": _json_array(normalized["source_refs"]),
                        "primary_point_node_ids": normalized["primary_point_node_ids"],
                        "primary_canonical_point_ids": normalized["primary_canonical_point_ids"],
                        "source_placement_node_ids": normalized["source_placement_node_ids"],
                        "metadata": _json(normalized["metadata"]),
                        "actor": user.id,
                    },
                )
                .mappings()
                .first()
            )
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
            inserted = dict(row)
        else:
            inserted = _insert_question(
                session,
                experiment_id=draft["experiment_id"],
                payload=payload,
                bank_kind="generated",
                actor_user_id=user.id,
                generation_id=str(draft["generation_id"]),
            )
        session.execute(
            text(
                """
                UPDATE experiment_question_drafts
                SET payload = CAST(:payload AS jsonb), status = 'published', updated_at = now()
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {"id": draft_id, "payload": _json(payload)},
        )
    return inserted


def reject_question_draft(
    *,
    draft_id: str,
) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE experiment_question_drafts
                    SET status = 'rejected', updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    RETURNING *
                    """
                ),
                {"id": draft_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return dict(row)
