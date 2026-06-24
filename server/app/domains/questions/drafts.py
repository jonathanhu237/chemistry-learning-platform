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
    _validate_question_payload,
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
    filters = ["1 = 1"]
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
        if not question_payload_has_catalog_evidence_lineage(payload):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": ["catalog-node evidence lineage is required before publication"]},
            )
        payload["status"] = "published"
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
