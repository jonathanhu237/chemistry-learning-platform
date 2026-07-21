from __future__ import annotations

import json
import urllib.error
from collections.abc import Callable
from typing import Any

from sqlalchemy import text

from server.app.domains.textbook_ingestion.errors import TextbookIngestionError
from server.app.domains.textbook_ingestion.repository import get_textbook_document
from server.app.domains.textbook_ingestion.storage import LocalTextbookBlobStore, TextbookStorageError
from server.app.domains.textbook_rag.index import TextbookElasticsearchClient
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


PublicationCleanup = Callable[[str], dict[str, Any]]
BlobCleanup = Callable[[str], None]


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _require_postgres_feature() -> None:
    settings = get_settings()
    if not settings.textbook_ingestion_enabled:
        raise TextbookIngestionError(
            "textbook_ingestion_disabled",
            "Online textbook ingestion is not enabled",
            status_code=409,
        )
    if settings.data_backend != "postgres":
        raise TextbookIngestionError(
            "postgres_required",
            "Online textbook ingestion requires the PostgreSQL data backend",
            status_code=503,
        )


def _document_for_update(session: Any, document_id: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
                SELECT *
                FROM source_documents
                WHERE id = :document_id
                  AND document_kind IN ('textbook', 'canonical_textbook')
                FOR UPDATE
                """
            ),
            {"document_id": document_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise TextbookIngestionError("textbook_not_found", "Textbook document not found", status_code=404)
    result = dict(row)
    result["metadata"] = dict(result.get("metadata") or {})
    result["quality_summary"] = dict(result.get("quality_summary") or {})
    return result


def _latest_job_for_update(session: Any, document_id: str) -> dict[str, Any] | None:
    row = (
        session.execute(
            text(
                """
                SELECT *
                FROM textbook_ingestion_jobs
                WHERE document_id = :document_id
                ORDER BY created_at DESC
                LIMIT 1
                FOR UPDATE
                """
            ),
            {"document_id": document_id},
        )
        .mappings()
        .first()
    )
    if not row:
        return None
    result = dict(row)
    result["quality_report"] = dict(result.get("quality_report") or {})
    result["outputs"] = dict(result.get("outputs") or {})
    return result


def _is_seed_document(document: dict[str, Any]) -> bool:
    return str(document.get("document_kind") or "") == "canonical_textbook"


def publication_blockers(
    document: dict[str, Any],
    latest_job: dict[str, Any] | None,
    *,
    chunk_count: int,
) -> list[str]:
    """Return stable machine-readable reasons why a version cannot become active."""

    status = str(document.get("publication_status") or "")
    if status == "published":
        return []
    if status not in {"review_ready", "inactive"}:
        return ["document_not_review_ready"]
    if chunk_count <= 0:
        return ["no_chunks"]
    if _is_seed_document(document):
        return [] if status == "inactive" else ["seed_document_not_rollback_candidate"]
    if not latest_job:
        return ["ingestion_job_missing"]

    blockers: list[str] = []
    job_status = str(latest_job.get("status") or "")
    allowed_job_statuses = {"review_ready"} if status == "review_ready" else {"review_ready", "ready"}
    if job_status not in allowed_job_statuses:
        blockers.append("ingestion_not_review_ready")

    quality_report = latest_job.get("quality_report")
    quality = dict(quality_report) if isinstance(quality_report, dict) else {}
    blockers.extend(str(item) for item in quality.get("blocking_issues") or [])
    if not bool(quality.get("publishable")):
        blockers.append("quality_not_publishable")

    outputs_value = latest_job.get("outputs")
    outputs = dict(outputs_value) if isinstance(outputs_value, dict) else {}
    if not bool(outputs.get("index_verified")):
        blockers.append("index_not_verified")

    total_chunks = int(latest_job.get("total_chunks") or 0)
    embedded_chunks = int(latest_job.get("embedded_chunks") or 0)
    indexed_chunks = int(latest_job.get("indexed_chunks") or 0)
    projected_chunks = int(outputs.get("indexed_chunks") or 0)
    if total_chunks <= 0 or total_chunks != chunk_count:
        blockers.append("chunk_count_mismatch")
    if embedded_chunks != total_chunks:
        blockers.append("embedding_count_mismatch")
    if indexed_chunks != total_chunks or projected_chunks != total_chunks:
        blockers.append("index_count_mismatch")
    return list(dict.fromkeys(blockers))


def _chunk_count(session: Any, document_id: str) -> int:
    return int(
        session.execute(
            text("SELECT count(*) FROM source_chunks WHERE document_id = :document_id"),
            {"document_id": document_id},
        ).scalar_one()
    )


def _bump_corpus_revision(
    session: Any,
    *,
    action: str,
    document_id: str,
    actor_id: str | None,
) -> int:
    revision = session.execute(
        text(
            """
            UPDATE textbook_corpus_state
            SET revision = revision + 1,
                last_action = :action,
                last_document_id = :document_id,
                updated_by = CAST(:actor_id AS uuid),
                updated_at = now()
            WHERE singleton_key = 1
            RETURNING revision
            """
        ),
        {"action": action, "document_id": document_id, "actor_id": actor_id},
    ).scalar_one_or_none()
    if revision is None:
        raise TextbookIngestionError(
            "textbook_corpus_state_missing",
            "Textbook corpus state is not initialized; apply database migrations",
            status_code=503,
        )
    return int(revision)


def _mark_corpus_evidence_stale(session: Any, *, revision: int, reason: str) -> dict[str, int]:
    diagnostic = _json({"textbook_corpus": {"revision": revision, "reason": reason}})
    binding_result = session.execute(
        text(
            """
            UPDATE experiment_catalog_point_evidence_bindings
            SET freshness_status = 'stale',
                selection_status = CASE
                  WHEN selection_status = 'selected' THEN 'stale'
                  ELSE selection_status
                END,
                diagnostics = COALESCE(diagnostics, '{}'::jsonb) || CAST(:diagnostic AS jsonb),
                updated_at = now()
            WHERE freshness_status <> 'stale'
               OR selection_status = 'selected'
            """
        ),
        {"diagnostic": diagnostic},
    )
    state_rows = [
        str(value)
        for value in session.execute(
            text("SELECT node_id FROM experiment_catalog_point_evidence_state ORDER BY node_id")
        ).scalars()
    ]
    state_result = session.execute(
        text(
            """
            UPDATE experiment_catalog_point_evidence_state
            SET evidence_status = 'stale',
                stale_reason = :reason,
                stale_at = now(),
                diagnostics = COALESCE(diagnostics, '{}'::jsonb) || CAST(:diagnostic AS jsonb),
                updated_at = now()
            """
        ),
        {"reason": reason, "diagnostic": diagnostic},
    )

    queued = 0
    if get_settings().catalog_point_evidence_auto_refresh:
        from server.app.domains.catalog_tree.jobs import queue_rag_evidence_refresh_job

        for node_id in state_rows:
            queue_rag_evidence_refresh_job(
                session,
                node_id=node_id,
                trigger_source="automatic",
                reason=reason,
                payload={"textbook_corpus_revision": revision},
            )
            queued += 1
    return {
        "states_staled": max(int(state_result.rowcount or 0), 0),
        "bindings_staled": max(int(binding_result.rowcount or 0), 0),
        "refresh_jobs_queued": queued,
    }


def _record_lifecycle_event(
    session: Any,
    *,
    document_id: str,
    job_id: str | None,
    action: str,
    actor_id: str | None,
    previous_status: str,
    new_status: str,
    corpus_revision: int | None,
    details: dict[str, Any],
) -> None:
    session.execute(
        text(
            """
            INSERT INTO textbook_lifecycle_events (
              document_id, job_id, action, actor_id, details,
              previous_publication_status, new_publication_status, corpus_revision
            )
            VALUES (
              :document_id, CAST(:job_id AS uuid), :action, CAST(:actor_id AS uuid),
              CAST(:details AS jsonb), :previous_status, :new_status, :corpus_revision
            )
            """
        ),
        {
            "document_id": document_id,
            "job_id": job_id,
            "action": action,
            "actor_id": actor_id,
            "details": _json(details),
            "previous_status": previous_status,
            "new_status": new_status,
            "corpus_revision": corpus_revision,
        },
    )


def publish_textbook(document_id: str, *, actor_id: str | None) -> dict[str, Any]:
    """Publish a review-ready version, or reactivate an inactive version as rollback."""

    _require_postgres_feature()
    no_change = False
    with db_session() as session:
        document = _document_for_update(session, document_id)
        logical_key = str(document["logical_textbook_key"])
        session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:logical_key))"), {"logical_key": logical_key})
        current_status = str(document.get("publication_status") or "")
        if current_status == "published":
            no_change = True
        else:
            latest_job = _latest_job_for_update(session, document_id)
            blockers = publication_blockers(document, latest_job, chunk_count=_chunk_count(session, document_id))
            if blockers:
                raise TextbookIngestionError(
                    "textbook_publish_blocked",
                    "Textbook version has not passed every publication gate",
                    status_code=409,
                    blockers=blockers,
                )

            active_rows = [
                dict(row)
                for row in session.execute(
                    text(
                        """
                        SELECT id, publication_status, version_number, document_kind
                        FROM source_documents
                        WHERE logical_textbook_key = :logical_key
                          AND publication_status = 'published'
                          AND id <> :document_id
                        FOR UPDATE
                        """
                    ),
                    {"logical_key": logical_key, "document_id": document_id},
                )
                .mappings()
                .all()
            ]
            replaced_ids = [str(row["id"]) for row in active_rows]
            if replaced_ids:
                session.execute(
                    text(
                        """
                        UPDATE source_documents
                        SET publication_status = 'inactive',
                            deactivated_at = now(),
                            deactivated_by = CAST(:actor_id AS uuid),
                            updated_at = now()
                        WHERE id = ANY(CAST(:document_ids AS text[]))
                        """
                    ),
                    {"document_ids": replaced_ids, "actor_id": actor_id},
                )
                session.execute(
                    text(
                        """
                        UPDATE source_chunks
                        SET content_status = 'archived', updated_at = now()
                        WHERE document_id = ANY(CAST(:document_ids AS text[]))
                        """
                    ),
                    {"document_ids": replaced_ids},
                )

            action = "rollback" if current_status == "inactive" else "publish"
            revision = _bump_corpus_revision(
                session,
                action=action,
                document_id=document_id,
                actor_id=actor_id,
            )
            session.execute(
                text(
                    """
                    UPDATE source_documents
                    SET publication_status = 'published',
                        processing_status = CASE
                          WHEN document_kind = 'textbook' THEN 'ready'
                          ELSE processing_status
                        END,
                        published_at = now(),
                        published_by = CAST(:actor_id AS uuid),
                        deactivated_at = NULL,
                        deactivated_by = NULL,
                        corpus_revision = :revision,
                        updated_at = now()
                    WHERE id = :document_id
                    """
                ),
                {"document_id": document_id, "actor_id": actor_id, "revision": revision},
            )
            session.execute(
                text(
                    """
                    UPDATE source_chunks
                    SET content_status = 'published',
                        review_required = false,
                        published_at = now(),
                        updated_at = now()
                    WHERE document_id = :document_id
                    """
                ),
                {"document_id": document_id},
            )
            if latest_job:
                session.execute(
                    text(
                        """
                        UPDATE textbook_ingestion_jobs
                        SET status = 'ready', progress = 100,
                            worker_id = NULL, lease_token = NULL, lease_expires_at = NULL,
                            finished_at = COALESCE(finished_at, now()), updated_at = now()
                        WHERE id = CAST(:job_id AS uuid)
                          AND status IN ('review_ready', 'ready')
                        """
                    ),
                    {"job_id": str(latest_job["id"])},
                )
                if str(latest_job.get("status")) == "review_ready":
                    session.execute(
                        text(
                            """
                            INSERT INTO textbook_ingestion_job_events (
                              job_id, status, progress, event_type, message, details
                            ) VALUES (
                              CAST(:job_id AS uuid), 'ready', 100, 'published',
                              'Textbook version published to the active RAG corpus', CAST(:details AS jsonb)
                            )
                            """
                        ),
                        {
                            "job_id": str(latest_job["id"]),
                            "details": _json({"corpus_revision": revision, "replaced_document_ids": replaced_ids}),
                        },
                    )

            stale = _mark_corpus_evidence_stale(
                session,
                revision=revision,
                reason=f"textbook_corpus_revision:{revision}",
            )
            _record_lifecycle_event(
                session,
                document_id=document_id,
                job_id=str(latest_job["id"]) if latest_job else None,
                action=action,
                actor_id=actor_id,
                previous_status=current_status,
                new_status="published",
                corpus_revision=revision,
                details={"replaced_document_ids": replaced_ids, "evidence": stale},
            )

    result = get_textbook_document(document_id)
    if no_change:
        result["lifecycle_noop"] = True
    return result


def deactivate_textbook(document_id: str, *, actor_id: str | None) -> dict[str, Any]:
    _require_postgres_feature()
    with db_session() as session:
        document = _document_for_update(session, document_id)
        logical_key = str(document["logical_textbook_key"])
        session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:logical_key))"), {"logical_key": logical_key})
        current_status = str(document.get("publication_status") or "")
        if current_status != "published":
            raise TextbookIngestionError(
                "textbook_not_published",
                "Only the published textbook version can be deactivated",
                status_code=409,
                publication_status=current_status,
            )
        latest_job = _latest_job_for_update(session, document_id)
        revision = _bump_corpus_revision(
            session,
            action="deactivate",
            document_id=document_id,
            actor_id=actor_id,
        )
        session.execute(
            text(
                """
                UPDATE source_documents
                SET publication_status = 'inactive',
                    deactivated_at = now(),
                    deactivated_by = CAST(:actor_id AS uuid),
                    corpus_revision = :revision,
                    updated_at = now()
                WHERE id = :document_id
                """
            ),
            {"document_id": document_id, "actor_id": actor_id, "revision": revision},
        )
        session.execute(
            text(
                """
                UPDATE source_chunks
                SET content_status = 'archived', updated_at = now()
                WHERE document_id = :document_id
                """
            ),
            {"document_id": document_id},
        )
        stale = _mark_corpus_evidence_stale(
            session,
            revision=revision,
            reason=f"textbook_corpus_revision:{revision}",
        )
        _record_lifecycle_event(
            session,
            document_id=document_id,
            job_id=str(latest_job["id"]) if latest_job else None,
            action="deactivate",
            actor_id=actor_id,
            previous_status=current_status,
            new_status="inactive",
            corpus_revision=revision,
            details={"evidence": stale},
        )
    return get_textbook_document(document_id)


def _delete_elasticsearch_projection(document_id: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.textbook_rag_elasticsearch_url:
        raise TextbookIngestionError(
            "elasticsearch_cleanup_unavailable",
            "Elasticsearch must be configured before deleting an indexed textbook",
            status_code=503,
        )
    client = TextbookElasticsearchClient(
        base_url=settings.textbook_rag_elasticsearch_url,
        index=settings.textbook_rag_elasticsearch_index,
        timeout=settings.textbook_rag_timeout_seconds,
    )
    try:
        response = client.request(
            "POST",
            f"/{client.index}/_delete_by_query?conflicts=proceed&refresh=true",
            {"query": {"term": {"document_id": document_id}}},
        )
        count_response = client.request(
            "POST",
            f"/{client.index}/_count",
            {"query": {"term": {"document_id": document_id}}},
        )
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"deleted": 0, "index_missing": True}
        raise TextbookIngestionError(
            "elasticsearch_cleanup_failed",
            "Elasticsearch rejected textbook cleanup",
            status_code=502,
            http_status=exc.code,
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise TextbookIngestionError(
            "elasticsearch_cleanup_failed",
            "Elasticsearch textbook cleanup is unavailable",
            status_code=502,
            error_type=exc.__class__.__name__,
        ) from exc
    remaining = int(count_response.get("count") or 0) if isinstance(count_response, dict) else 0
    if remaining:
        raise TextbookIngestionError(
            "elasticsearch_cleanup_incomplete",
            "Elasticsearch retained chunks for the deleted textbook",
            status_code=502,
            remaining=remaining,
        )
    return {"deleted": int(response.get("deleted") or 0), "index_missing": False}


def delete_textbook(
    document_id: str,
    *,
    actor_id: str | None,
    projection_cleanup: PublicationCleanup | None = None,
    blob_cleanup: BlobCleanup | None = None,
) -> dict[str, Any]:
    """Explicitly delete an unpublished online PDF and its ES-derived projection.

    PostgreSQL facts and audit rows are retained as a tombstone. This keeps the
    action reviewable while the original blob and rebuildable ES projection are
    physically removed.
    """

    _require_postgres_feature()
    settings = get_settings()
    with db_session() as session:
        document = _document_for_update(session, document_id)
        logical_key = str(document["logical_textbook_key"])
        session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:logical_key))"), {"logical_key": logical_key})
        current_status = str(document.get("publication_status") or "")
        if _is_seed_document(document):
            raise TextbookIngestionError(
                "seed_textbook_delete_forbidden",
                "Canonical seed textbooks are retained for rollback",
                status_code=409,
            )
        if current_status == "published":
            raise TextbookIngestionError(
                "published_textbook_delete_forbidden",
                "Deactivate the textbook before explicit deletion",
                status_code=409,
            )
        if current_status == "deleted":
            raise TextbookIngestionError("textbook_already_deleted", "Textbook was already deleted", status_code=409)

        latest_job = _latest_job_for_update(session, document_id)
        active_job_statuses = {
            "uploaded",
            "extracting",
            "awaiting_ocr",
            "ocr",
            "structuring",
            "chunking",
            "embedding",
            "indexing",
        }
        if latest_job and str(latest_job.get("status") or "") in active_job_statuses:
            raise TextbookIngestionError(
                "textbook_job_active",
                "Cancel the active ingestion job before deleting the textbook",
                status_code=409,
            )

        outputs = dict((latest_job or {}).get("outputs") or {})
        projection_possible = bool(outputs.get("index_verified")) or (
            int((latest_job or {}).get("indexed_chunks") or 0) > 0
        )
        projection_possible = projection_possible or int((latest_job or {}).get("progress") or 0) >= 88
        cleanup_result: dict[str, Any] = {"deleted": 0, "skipped": True}
        if projection_possible or settings.textbook_rag_elasticsearch_url:
            cleanup_result = (projection_cleanup or _delete_elasticsearch_projection)(document_id)

        relative_path = str(document.get("path") or "")
        try:
            (blob_cleanup or LocalTextbookBlobStore(settings.textbook_storage_root).delete)(relative_path)
        except (TextbookStorageError, OSError) as exc:
            raise TextbookIngestionError(
                "textbook_blob_cleanup_failed",
                "The original textbook PDF could not be deleted safely",
                status_code=500,
                error_type=exc.__class__.__name__,
            ) from exc
        session.execute(
            text(
                """
                UPDATE source_documents
                SET publication_status = 'deleted',
                    processing_status = 'deleted',
                    deleted_at = now(),
                    deleted_by = CAST(:actor_id AS uuid),
                    metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata AS jsonb),
                    updated_at = now()
                WHERE id = :document_id
                """
            ),
            {
                "document_id": document_id,
                "actor_id": actor_id,
                "metadata": _json({"original_blob_deleted": True, "elasticsearch_cleanup": cleanup_result}),
            },
        )
        session.execute(
            text(
                """
                UPDATE source_chunks
                SET content_status = 'archived', updated_at = now()
                WHERE document_id = :document_id
                """
            ),
            {"document_id": document_id},
        )
        _record_lifecycle_event(
            session,
            document_id=document_id,
            job_id=str(latest_job["id"]) if latest_job else None,
            action="delete",
            actor_id=actor_id,
            previous_status=current_status,
            new_status="deleted",
            corpus_revision=None,
            details={"original_blob_deleted": True, "elasticsearch_cleanup": cleanup_result},
        )
    return get_textbook_document(document_id)
