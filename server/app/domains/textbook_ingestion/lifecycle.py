from __future__ import annotations

import json
import urllib.error
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from server.app.domains.textbook_ingestion.config import effective_ingestion_settings
from server.app.domains.textbook_ingestion.errors import TextbookIngestionError
from server.app.domains.textbook_ingestion.projection import elasticsearch_operation_issues
from server.app.domains.textbook_ingestion.repository import get_textbook_document
from server.app.domains.textbook_ingestion.storage import LocalTextbookBlobStore
from server.app.domains.textbook_rag.index import TextbookElasticsearchClient
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import Settings, get_settings


PublicationCleanup = Callable[[str], dict[str, Any]]
BlobCleanup = Callable[[str], None]
ProjectionVerifier = Callable[[dict[str, Any], dict[str, Any] | None, int], dict[str, Any]]


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


def _projection_identity(document: dict[str, Any]) -> tuple[str, str]:
    if not _is_seed_document(document):
        return "document_id", str(document["id"])
    metadata = dict(document.get("metadata") or {})
    index_document_id = str(metadata.get("index_document_id") or "").strip()
    if not index_document_id:
        raise TextbookIngestionError(
            "textbook_projection_identity_missing",
            "The canonical textbook does not declare its Elasticsearch document identity",
            status_code=409,
        )
    return "doc_id", index_document_id


def _expected_projection_contract(
    document: dict[str, Any],
    latest_job: dict[str, Any] | None,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or effective_ingestion_settings()
    job = latest_job or {}
    snapshot = dict(job.get("config_snapshot") or {})
    snapshot_embedding = dict(snapshot.get("embedding") or {})
    outputs = dict(job.get("outputs") or {})
    embedding_model = str(
        settings.textbook_rag_embedding_model
        or snapshot_embedding.get("model")
        or outputs.get("embedding_model")
        or ""
    ).strip()
    embedding_dimension = int(
        settings.textbook_rag_embedding_dimension
        or snapshot_embedding.get("dimension")
        or outputs.get("embedding_dimension")
        or 0
    )
    processing_fingerprint = ""
    projection_run_id = ""
    job_projection_run_id = str(outputs.get("projection_run_id") or "").strip()
    if not _is_seed_document(document):
        processing_fingerprint = str(
            document.get("processing_fingerprint")
            or job.get("processing_fingerprint")
            or ""
        ).strip()
        projection_run_id = str(document.get("active_projection_run_id") or "").strip()
    return {
        "embedding_model": embedding_model,
        "embedding_dimension": embedding_dimension,
        "processing_fingerprint": processing_fingerprint,
        "projection_run_id": projection_run_id,
        "job_projection_run_id": job_projection_run_id,
    }


def verify_live_elasticsearch_projection(
    document: dict[str, Any],
    latest_job: dict[str, Any] | None,
    expected_chunk_count: int,
    *,
    client: TextbookElasticsearchClient | None = None,
) -> dict[str, Any]:
    """Verify the current shared-index projection instead of trusting job history."""

    settings = effective_ingestion_settings()
    if client is None:
        if not settings.textbook_rag_elasticsearch_url:
            raise TextbookIngestionError(
                "elasticsearch_verification_unavailable",
                "Elasticsearch must be configured before publishing a textbook",
                status_code=503,
            )
        client = TextbookElasticsearchClient(
            base_url=settings.textbook_rag_elasticsearch_url,
            index=settings.textbook_rag_elasticsearch_index,
            timeout=settings.textbook_rag_timeout_seconds,
        )

    identity_field, identity_value = _projection_identity(document)
    expected = _expected_projection_contract(document, latest_job, settings=settings)
    blockers: list[str] = []
    if not expected["embedding_model"]:
        blockers.append("embedding_model_unavailable")
    if int(expected["embedding_dimension"] or 0) <= 0:
        blockers.append("embedding_dimension_unavailable")
    if not _is_seed_document(document):
        if not expected["processing_fingerprint"]:
            blockers.append("processing_fingerprint_unavailable")
        if not expected["projection_run_id"]:
            blockers.append("active_projection_run_id_missing")
        current_status = str(document.get("publication_status") or "")
        if not expected["job_projection_run_id"] and current_status != "inactive":
            blockers.append("job_projection_run_id_missing")
        if (
            expected["job_projection_run_id"]
            and expected["job_projection_run_id"] != expected["projection_run_id"]
        ):
            blockers.append("projection_run_id_mismatch")

    try:
        mapping_response = client.request("GET", f"/{client.index}/_mapping")
        count_response = client.request(
            "POST",
            f"/{client.index}/_count",
            {"query": {"term": {identity_field: identity_value}}},
        )
        filters: list[dict[str, Any]] = [{"term": {identity_field: identity_value}}]
        if expected["embedding_model"]:
            filters.append({"term": {"embedding_model": expected["embedding_model"]}})
        if int(expected["embedding_dimension"] or 0) > 0:
            filters.append({"term": {"embedding_dimension": expected["embedding_dimension"]}})
        if expected["processing_fingerprint"]:
            filters.append(
                {"term": {"processing_fingerprint": expected["processing_fingerprint"]}}
            )
        if expected["projection_run_id"]:
            filters.append({"term": {"projection_run_id": expected["projection_run_id"]}})
        contract_count_response = client.request(
            "POST",
            f"/{client.index}/_count",
            {"query": {"bool": {"filter": filters}}},
        )
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            blockers.append("elasticsearch_index_missing")
            mapping_response = {}
            count_response = {}
            contract_count_response = {}
        else:
            raise TextbookIngestionError(
                "elasticsearch_verification_failed",
                "Elasticsearch rejected textbook publication verification",
                status_code=502,
                http_status=exc.code,
            ) from exc
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise TextbookIngestionError(
            "elasticsearch_verification_failed",
            "Elasticsearch textbook publication verification is unavailable",
            status_code=502,
            error_type=exc.__class__.__name__,
        ) from exc

    index_mapping = (
        mapping_response.get(client.index, {})
        if isinstance(mapping_response, dict)
        else {}
    )
    mappings = index_mapping.get("mappings", {}) if isinstance(index_mapping, dict) else {}
    mapping_metadata = mappings.get("_meta", {}) if isinstance(mappings, dict) else {}
    properties = mappings.get("properties", {}) if isinstance(mappings, dict) else {}
    embedding_property = (
        properties.get("embedding", {}) if isinstance(properties, dict) else {}
    )
    actual_model = str(mapping_metadata.get("embedding_model") or "")
    actual_dimension = int(
        mapping_metadata.get("embedding_dimension")
        or (
            embedding_property.get("dims")
            if isinstance(embedding_property, dict)
            else 0
        )
        or 0
    )
    actual_count = (
        int(count_response.get("count") or 0) if isinstance(count_response, dict) else 0
    )
    contract_count = (
        int(contract_count_response.get("count") or 0)
        if isinstance(contract_count_response, dict)
        else 0
    )
    count_failed_shards = int(
        dict(count_response.get("_shards") or {}).get("failed") or 0
    ) if isinstance(count_response, dict) else 0
    contract_failed_shards = int(
        dict(contract_count_response.get("_shards") or {}).get("failed") or 0
    ) if isinstance(contract_count_response, dict) else 0
    count_issues = elasticsearch_operation_issues(count_response)
    contract_count_issues = elasticsearch_operation_issues(contract_count_response)
    if count_issues or contract_count_issues:
        blockers.append("elasticsearch_count_shards_failed")
    if expected["embedding_model"] and actual_model != expected["embedding_model"]:
        blockers.append("embedding_model_mismatch")
    if int(expected["embedding_dimension"] or 0) > 0 and actual_dimension != int(
        expected["embedding_dimension"]
    ):
        blockers.append("embedding_dimension_mismatch")
    if contract_count != expected_chunk_count:
        blockers.append("live_active_projection_count_mismatch")
    stale_projection_count = max(actual_count - contract_count, 0)

    return {
        "verified": not blockers,
        "index_name": client.index,
        "identity_field": identity_field,
        "identity_value": identity_value,
        "expected_chunk_count": expected_chunk_count,
        "actual_chunk_count": actual_count,
        "contract_chunk_count": contract_count,
        "stale_projection_chunk_count": stale_projection_count,
        "count_failed_shards": count_failed_shards,
        "contract_count_failed_shards": contract_failed_shards,
        "count_issues": count_issues,
        "contract_count_issues": contract_count_issues,
        "expected_embedding_model": expected["embedding_model"],
        "actual_embedding_model": actual_model,
        "expected_embedding_dimension": expected["embedding_dimension"],
        "actual_embedding_dimension": actual_dimension,
        "processing_fingerprint": expected["processing_fingerprint"] or None,
        "active_projection_run_id": expected["projection_run_id"] or None,
        "job_projection_run_id": expected["job_projection_run_id"] or None,
        "blockers": list(dict.fromkeys(blockers)),
    }


def _require_live_projection(
    verifier: ProjectionVerifier,
    document: dict[str, Any],
    latest_job: dict[str, Any] | None,
    chunk_count: int,
) -> dict[str, Any]:
    try:
        result = verifier(document, latest_job, chunk_count)
    except TextbookIngestionError:
        raise
    except Exception as exc:
        raise TextbookIngestionError(
            "elasticsearch_verification_failed",
            "Elasticsearch textbook publication verification failed",
            status_code=502,
            error_type=exc.__class__.__name__,
        ) from exc
    if not isinstance(result, dict) or not bool(result.get("verified")):
        blockers = (
            [str(item) for item in result.get("blockers") or []]
            if isinstance(result, dict)
            else []
        )
        raise TextbookIngestionError(
            "textbook_publish_blocked",
            "The live Elasticsearch projection does not match PostgreSQL textbook facts",
            status_code=409,
            blockers=blockers or ["live_projection_not_verified"],
            verification=result if isinstance(result, dict) else {},
        )
    return result


def publication_blockers(
    document: dict[str, Any],
    latest_job: dict[str, Any] | None,
    *,
    chunk_count: int,
) -> list[str]:
    """Return stable machine-readable reasons why a version cannot become active."""

    status = str(document.get("publication_status") or "")
    if status == "published":
        return [] if chunk_count > 0 else ["no_chunks"]
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
) -> str:
    event_id = session.execute(
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
            RETURNING id
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
    ).scalar_one()
    return str(event_id)


def publish_textbook(
    document_id: str,
    *,
    actor_id: str | None,
    projection_verifier: ProjectionVerifier | None = None,
) -> dict[str, Any]:
    """Publish a review-ready version, or reactivate an inactive version as rollback."""

    _require_postgres_feature()
    no_change = False
    with db_session() as session:
        document = _document_for_update(session, document_id)
        logical_key = str(document["logical_textbook_key"])
        session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:logical_key))"), {"logical_key": logical_key})
        current_status = str(document.get("publication_status") or "")
        latest_job = _latest_job_for_update(session, document_id)
        chunk_count = _chunk_count(session, document_id)
        blockers = publication_blockers(document, latest_job, chunk_count=chunk_count)
        if blockers:
            raise TextbookIngestionError(
                "textbook_publish_blocked",
                "Textbook version has not passed every publication gate",
                status_code=409,
                blockers=blockers,
            )
        live_verification = _require_live_projection(
            projection_verifier or verify_live_elasticsearch_projection,
            document,
            latest_job,
            chunk_count,
        )
        if current_status == "published":
            no_change = True
        else:
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
                details={
                    "replaced_document_ids": replaced_ids,
                    "evidence": stale,
                    "projection_verification": live_verification,
                },
            )

    result = get_textbook_document(document_id)
    result["projection_verification"] = live_verification
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
    settings = effective_ingestion_settings()
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
    delete_issues = elasticsearch_operation_issues(response)
    count_issues = elasticsearch_operation_issues(count_response)
    if delete_issues or count_issues:
        raise TextbookIngestionError(
            "elasticsearch_cleanup_incomplete",
            "Elasticsearch did not confirm complete textbook cleanup across every shard",
            status_code=502,
            delete_issues=delete_issues,
            count_issues=count_issues,
        )
    remaining = int(count_response.get("count") or 0) if isinstance(count_response, dict) else 0
    if remaining:
        raise TextbookIngestionError(
            "elasticsearch_cleanup_incomplete",
            "Elasticsearch retained chunks for the deleted textbook",
            status_code=502,
            remaining=remaining,
        )
    return {"deleted": int(response.get("deleted") or 0), "index_missing": False}


def _cleanup_failure(exc: Exception) -> dict[str, Any]:
    return {
        "status": "failed",
        "reason": str(getattr(exc, "reason", "") or exc.__class__.__name__).lower()[:120],
        "error_type": exc.__class__.__name__,
    }


def _cleanup_complete(previous: dict[str, Any], stage: str) -> bool:
    value = previous.get(stage)
    return isinstance(value, dict) and str(value.get("status") or "") in {
        "complete",
        "skipped",
    }


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
    rag_settings = effective_ingestion_settings()
    cleanup_event_id = ""
    cleanup_noop = False
    projection_should_run = False
    blob_should_run = False
    relative_path = ""
    previous_cleanup: dict[str, Any] = {}
    cleanup_attempt = 0

    # Commit the unpublishable fact and audit trail before touching either
    # external system. A later cleanup or commit failure can therefore never
    # leave a publishable document whose projection/blob is missing.
    with db_session() as session:
        document = _document_for_update(session, document_id)
        logical_key = str(document["logical_textbook_key"])
        session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:logical_key))"),
            {"logical_key": logical_key},
        )
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
        if (
            current_status != "deleted"
            and latest_job
            and str(latest_job.get("status") or "") in active_job_statuses
        ):
            raise TextbookIngestionError(
                "textbook_job_active",
                "Cancel the active ingestion job before deleting the textbook",
                status_code=409,
            )

        metadata = dict(document.get("metadata") or {})
        previous_cleanup = dict(metadata.get("deletion_cleanup") or {})
        if current_status == "deleted" and previous_cleanup.get("status") == "complete":
            cleanup_noop = True
        else:
            outputs = dict((latest_job or {}).get("outputs") or {})
            projection_possible = bool(outputs.get("index_verified")) or (
                int((latest_job or {}).get("indexed_chunks") or 0) > 0
            )
            projection_possible = projection_possible or int(
                (latest_job or {}).get("progress") or 0
            ) >= 88
            projection_should_run = not _cleanup_complete(previous_cleanup, "projection") and bool(
                projection_cleanup
                or rag_settings.textbook_rag_elasticsearch_url
                or projection_possible
            )
            blob_should_run = not _cleanup_complete(previous_cleanup, "blob")
            cleanup_attempt = int(previous_cleanup.get("attempt") or 0) + 1
            pending_cleanup = {
                "status": "pending",
                "attempt": cleanup_attempt,
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "projection": (
                    {"status": "pending"}
                    if projection_should_run
                    else previous_cleanup.get("projection")
                    or {"status": "skipped", "reason": "projection_not_detected_or_configured"}
                ),
                "blob": (
                    {"status": "pending"}
                    if blob_should_run
                    else previous_cleanup.get("blob")
                    or {"status": "complete"}
                ),
            }
            relative_path = str(document.get("path") or "")
            session.execute(
                text(
                    """
                    UPDATE source_documents
                    SET publication_status = 'deleted',
                        processing_status = 'deleted',
                        active_projection_run_id = NULL,
                        deleted_at = COALESCE(deleted_at, now()),
                        deleted_by = COALESCE(deleted_by, CAST(:actor_id AS uuid)),
                        metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata AS jsonb),
                        updated_at = now()
                    WHERE id = :document_id
                    """
                ),
                {
                    "document_id": document_id,
                    "actor_id": actor_id,
                    "metadata": _json({"deletion_cleanup": pending_cleanup}),
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
            cleanup_event_id = _record_lifecycle_event(
                session,
                document_id=document_id,
                job_id=str(latest_job["id"]) if latest_job else None,
                action="delete",
                actor_id=actor_id,
                previous_status=current_status,
                new_status="deleted",
                corpus_revision=None,
                details={"phase": "cleanup_pending", "deletion_cleanup": pending_cleanup},
            )

    if cleanup_noop:
        result = get_textbook_document(document_id)
        result["lifecycle_noop"] = True
        return result

    projection_result = previous_cleanup.get("projection") or {
        "status": "skipped",
        "reason": "projection_not_detected_or_configured",
    }
    blob_result = previous_cleanup.get("blob") or {"status": "complete"}
    failures: list[str] = []
    if projection_should_run:
        try:
            raw_projection_result = (projection_cleanup or _delete_elasticsearch_projection)(
                document_id
            )
            projection_result = {"status": "complete", "result": raw_projection_result}
        except Exception as exc:
            projection_result = _cleanup_failure(exc)
            failures.append("projection")
    if blob_should_run:
        try:
            (blob_cleanup or LocalTextbookBlobStore(settings.textbook_storage_root).delete)(
                relative_path
            )
            blob_result = {"status": "complete"}
        except Exception as exc:
            blob_result = _cleanup_failure(exc)
            failures.append("blob")

    cleanup_result = {
        "status": "failed" if failures else "complete",
        "attempt": cleanup_attempt,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "projection": projection_result,
        "blob": blob_result,
        "failed_stages": failures,
    }
    compatibility_projection = (
        projection_result.get("result")
        if isinstance(projection_result, dict) and projection_result.get("status") == "complete"
        else projection_result
    )

    # Finalize the durable audit in a fresh transaction. If this commit fails,
    # the already-committed tombstone remains safe and a retry resumes cleanup.
    cleanup_superseded = False
    with db_session() as session:
        document = _document_for_update(session, document_id)
        if str(document.get("publication_status") or "") != "deleted":
            raise TextbookIngestionError(
                "textbook_delete_state_lost",
                "The textbook deletion tombstone is no longer present",
                status_code=409,
            )
        durable_cleanup = dict(dict(document.get("metadata") or {}).get("deletion_cleanup") or {})
        cleanup_superseded = int(durable_cleanup.get("attempt") or 0) != cleanup_attempt
        if not cleanup_superseded:
            session.execute(
                text(
                    """
                    UPDATE source_documents
                    SET metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata AS jsonb),
                        updated_at = now()
                    WHERE id = :document_id
                    """
                ),
                {
                    "document_id": document_id,
                    "metadata": _json(
                        {
                            "deletion_cleanup": cleanup_result,
                            "original_blob_deleted": blob_result.get("status") == "complete",
                            "elasticsearch_cleanup": compatibility_projection,
                        }
                    ),
                },
            )
        session.execute(
            text(
                """
                UPDATE textbook_lifecycle_events
                SET details = details || CAST(:details AS jsonb)
                WHERE id = CAST(:event_id AS uuid)
                """
            ),
            {
                "event_id": cleanup_event_id,
                "details": _json(
                    {
                        "phase": (
                            "cleanup_superseded"
                            if cleanup_superseded
                            else "cleanup_failed"
                            if failures
                            else "cleanup_complete"
                        ),
                        "deletion_cleanup": cleanup_result,
                        "original_blob_deleted": blob_result.get("status") == "complete",
                        "elasticsearch_cleanup": compatibility_projection,
                    }
                ),
            },
        )

    if cleanup_superseded:
        result = get_textbook_document(document_id)
        result["cleanup_superseded"] = True
        return result
    if failures:
        raise TextbookIngestionError(
            "textbook_delete_cleanup_failed",
            "The textbook is deleted and unpublishable, but external cleanup must be retried",
            status_code=502 if "projection" in failures else 500,
            failed_stages=failures,
            cleanup=cleanup_result,
        )
    return get_textbook_document(document_id)
