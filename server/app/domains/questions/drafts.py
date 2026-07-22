from __future__ import annotations

from typing import Any

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from sqlalchemy import text

from server.app.infrastructure.database import db_session
from server.app.experiment_admin_schemas import DraftUpdateRequest
from server.app.domains.questions.bank import (
    _insert_question,
    _json,
    _json_array,
    _question_draft_response,
    _question_withdrawal_provenance,
    _validate_question_payload,
    _without_question_withdrawal_provenance,
)
from server.app.domains.questions.duplicate_risk import attach_duplicate_risk_for_payload
from server.app.domains.questions.generation import question_payload_has_catalog_evidence_lineage
from server.app.domains.questions.point_identity import normalize_question_point_identity


def _withdrawal_provenance(row: dict[str, Any], *, strict: bool = False) -> dict[str, str] | None:
    try:
        return _question_withdrawal_provenance(row)
    except ValueError as exc:
        if strict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return None


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
                    SELECT d.*, g.prompt, g.mode, g.warning,
                           g.mode AS generation_mode,
                           g.metadata AS generation_metadata,
                           g.created_by AS generation_created_by,
                           g.created_at AS generation_created_at,
                           fe.code AS experiment_code, fe.title AS experiment_title
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
    items = [_question_draft_response(row, _withdrawal_provenance(row)) for row in rows]
    return {"items": items, "total": len(items)}


def update_question_draft(
    *,
    payload: DraftUpdateRequest,
    draft_id: str,
) -> dict[str, Any]:
    if payload.status not in {None, "draft"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Draft status transitions must use the publish or reject action",
        )
    with db_session() as session:
        draft = (
            session.execute(
                text(
                    """
                    SELECT d.*, g.mode AS generation_mode,
                           g.metadata AS generation_metadata,
                           g.created_by AS generation_created_by,
                           g.created_at AS generation_created_at
                    FROM experiment_question_drafts d
                    JOIN experiment_question_generations g ON g.id = d.generation_id
                    WHERE d.id = CAST(:id AS uuid)
                    FOR UPDATE OF d
                    """
                ),
                {"id": draft_id},
            )
            .mappings()
            .first()
        )
        if not draft:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
        if draft["status"] != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only active drafts can be updated")
        editable_payload = _without_question_withdrawal_provenance({**payload.payload, "status": "draft"})
        normalized, errors = _validate_question_payload(editable_payload)
        draft_payload = normalized or editable_payload
        draft_payload = attach_duplicate_risk_for_payload(
            session,
            payload=draft_payload,
            owner_kind="draft",
            owner_id=draft_id,
        )
        if normalized is not None and not question_payload_has_catalog_evidence_lineage(draft_payload):
            errors.append("catalog-node evidence lineage is required before publication")
        row = (
            session.execute(
                text(
                    """
                    UPDATE experiment_question_drafts
                    SET payload = CAST(:payload AS jsonb),
                        validation_errors = CAST(:errors AS jsonb),
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid) AND status = 'draft'
                    RETURNING *
                    """
                ),
                {
                    "id": draft_id,
                    "payload": _json(draft_payload),
                    "errors": _json_array(errors),
                },
            )
            .mappings()
            .first()
        )
        if not row:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Draft is no longer active")
        provenance = _withdrawal_provenance(dict(draft), strict=True)
    return _question_draft_response(dict(row), provenance)


def publish_question_draft(
    *,
    draft_id: str,
    user: Any,
) -> dict[str, Any]:
    with db_session() as session:
        draft = (
            session.execute(
                text(
                    """
                    SELECT d.*, g.mode AS generation_mode,
                           g.metadata AS generation_metadata,
                           g.created_by AS generation_created_by,
                           g.created_at AS generation_created_at
                    FROM experiment_question_drafts d
                    JOIN experiment_question_generations g ON g.id = d.generation_id
                    WHERE d.id = CAST(:id AS uuid)
                    FOR UPDATE OF d, g
                    """
                ),
                {"id": draft_id},
            )
            .mappings()
            .first()
        )
        if not draft:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
        if draft["status"] != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft questions can be published")
        payload = _without_question_withdrawal_provenance({**dict(draft["payload"] or {}), "status": "published"})
        normalized, errors = _validate_question_payload(payload)
        if errors or normalized is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"errors": errors})
        payload = normalize_question_point_identity(session, normalized)
        payload = attach_duplicate_risk_for_payload(
            session,
            payload=payload,
            owner_kind="draft",
            owner_id=draft_id,
        )
        if not question_payload_has_catalog_evidence_lineage(payload):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": ["catalog-node evidence lineage is required before publication"]},
            )
        payload["status"] = "published"
        provenance = _withdrawal_provenance(dict(draft), strict=True)
        if provenance:
            source = (
                session.execute(
                    text("SELECT * FROM experiment_questions WHERE id = CAST(:id AS uuid) FOR UPDATE"),
                    {"id": provenance["revoked_from_question_id"]},
                )
                .mappings()
                .first()
            )
            if not source:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Withdrawn source question no longer exists")
            expected_statuses = {"disabled"} if provenance["source_status"] == "disabled" else {"draft", "disabled"}
            if source["status"] not in expected_statuses:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Withdrawn source question is no longer in its withdrawn state",
                )
            if source["experiment_id"] != draft["experiment_id"]:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Withdrawal draft and source question belong to different experiments",
                )
            source_status = str(source["status"])
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
                        WHERE id = CAST(:id AS uuid) AND status = :source_status
                        RETURNING *
                        """
                    ),
                    {
                        "id": provenance["revoked_from_question_id"],
                        "generation_id": str(draft["generation_id"]),
                        "question_type": payload["question_type"],
                        "stem": payload["stem"],
                        "options": _json_array(payload["options"]),
                        "answer": _json(payload["answer"]),
                        "explanation": payload["explanation"],
                        "difficulty": payload["difficulty"],
                        "related_chapter_ids": payload["related_chapter_ids"],
                        "related_knowledge_point_ids": payload["related_knowledge_point_ids"],
                        "source_chunk_ids": payload["source_chunk_ids"],
                        "source_refs": _json_array(payload["source_refs"]),
                        "primary_point_node_ids": payload["primary_point_node_ids"],
                        "primary_canonical_point_ids": payload["primary_canonical_point_ids"],
                        "source_placement_node_ids": payload["source_placement_node_ids"],
                        "metadata": _json(payload["metadata"]),
                        "actor": user.id,
                        "source_status": source_status,
                    },
                )
                .mappings()
                .first()
            )
            if not row:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Withdrawn source question changed concurrently")
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
                SET payload = CAST(:payload AS jsonb), validation_errors = '[]'::jsonb,
                    status = 'published', updated_at = now()
                WHERE id = CAST(:id AS uuid) AND status = 'draft'
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
