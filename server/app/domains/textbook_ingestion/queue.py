from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from sqlalchemy import text

from server.app.domains.textbook_ingestion.config import (
    effective_ingestion_settings,
    processing_config_snapshot,
    processing_fingerprint,
)
from server.app.domains.textbook_ingestion.contracts import (
    ACTIVE_INGESTION_STAGES,
    IngestionStage,
    validate_stage_transition,
)
from server.app.domains.textbook_ingestion.errors import TextbookIngestionError, TextbookJobLeaseLostError
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


PROGRESS_COUNTERS = frozenset(
    {
        "total_pages",
        "processed_pages",
        "ocr_pages",
        "total_chunks",
        "embedded_chunks",
        "indexed_chunks",
    }
)


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


@dataclass(frozen=True)
class ClaimedIngestionJob:
    id: str
    document_id: str
    status: IngestionStage
    attempts: int
    max_attempts: int
    worker_id: str
    lease_token: str
    processing_fingerprint: str
    config_snapshot: dict[str, Any]
    cancellation_requested_at: datetime | None = None


def _claimed_job(row: Any) -> ClaimedIngestionJob:
    return ClaimedIngestionJob(
        id=str(row["id"]),
        document_id=str(row["document_id"]),
        status=IngestionStage(str(row["status"])),
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        worker_id=str(row["worker_id"]),
        lease_token=str(row["lease_token"]),
        processing_fingerprint=str(row["processing_fingerprint"]),
        config_snapshot=dict(row["config_snapshot"] or {}),
        cancellation_requested_at=row.get("cancellation_requested_at"),
    )


def _reap_stale_jobs(session: Any) -> dict[str, int]:
    cancelled = list(
        session.execute(
            text(
                """
                UPDATE textbook_ingestion_jobs
                SET status = 'cancelled',
                    worker_id = NULL,
                    lease_token = NULL,
                    lease_expires_at = NULL,
                    finished_at = now(),
                    updated_at = now()
                WHERE cancellation_requested_at IS NOT NULL
                  AND status IN ('uploaded', 'extracting', 'ocr', 'structuring', 'chunking', 'embedding', 'indexing')
                  AND (worker_id IS NULL OR lease_expires_at IS NULL OR lease_expires_at <= now())
                RETURNING id, document_id, progress
                """
            )
        )
        .mappings()
        .all()
    )
    exhausted = list(
        session.execute(
            text(
                """
                UPDATE textbook_ingestion_jobs
                SET status = 'failed',
                    error_code = 'attempts_exhausted',
                    error_message = 'Worker lease expired after the final permitted attempt',
                    worker_id = NULL,
                    lease_token = NULL,
                    lease_expires_at = NULL,
                    finished_at = now(),
                    updated_at = now()
                WHERE cancellation_requested_at IS NULL
                  AND attempts >= max_attempts
                  AND status IN ('uploaded', 'extracting', 'ocr', 'structuring', 'chunking', 'embedding', 'indexing')
                  AND (worker_id IS NULL OR lease_expires_at IS NULL OR lease_expires_at <= now())
                RETURNING id, document_id, progress
                """
            )
        )
        .mappings()
        .all()
    )
    for row in cancelled:
        session.execute(
            text(
                """
                INSERT INTO textbook_ingestion_job_events (
                  job_id, status, progress, event_type, message, details
                ) VALUES (
                  CAST(:job_id AS uuid), 'cancelled', :progress, 'cancelled',
                  'Cancellation finalized after the worker lease ended',
                  '{"reason":"stale_or_unclaimed_lease"}'::jsonb
                )
                """
            ),
            {"job_id": str(row["id"]), "progress": int(row["progress"] or 0)},
        )
        session.execute(
            text(
                """
                UPDATE source_documents
                SET processing_status = 'cancelled', publication_status = 'draft',
                    active_projection_run_id = NULL, updated_at = now()
                WHERE id = :document_id AND publication_status NOT IN ('published', 'deleted')
                """
            ),
            {"document_id": str(row["document_id"])},
        )
    for row in exhausted:
        session.execute(
            text(
                """
                INSERT INTO textbook_ingestion_job_events (
                  job_id, status, progress, event_type, message, details
                ) VALUES (
                  CAST(:job_id AS uuid), 'failed', :progress, 'failed',
                  'Worker lease expired after the final permitted attempt',
                  '{"error_code":"attempts_exhausted"}'::jsonb
                )
                """
            ),
            {"job_id": str(row["id"]), "progress": int(row["progress"] or 0)},
        )
        session.execute(
            text(
                """
                UPDATE source_documents
                SET processing_status = 'failed', publication_status = 'failed',
                    active_projection_run_id = NULL, updated_at = now()
                WHERE id = :document_id AND publication_status NOT IN ('published', 'deleted')
                """
            ),
            {"document_id": str(row["document_id"])},
        )
    return {"cancelled": len(cancelled), "failed": len(exhausted)}


def reap_stale_jobs() -> dict[str, int]:
    """Finalize dead-worker cancellations and exhausted leases."""

    with db_session() as session:
        return _reap_stale_jobs(session)


def claim_next_job(worker_id: str, *, lease_seconds: int | None = None) -> ClaimedIngestionJob | None:
    worker = worker_id.strip()
    if not worker:
        raise ValueError("worker_id is required")
    effective_lease_seconds = lease_seconds or get_settings().textbook_ingestion_lease_seconds
    with db_session() as session:
        _reap_stale_jobs(session)
        row = (
            session.execute(
                text(
                    """
                    WITH candidate AS (
                      SELECT tij.id
                      FROM textbook_ingestion_jobs tij
                      JOIN source_documents sd ON sd.id = tij.document_id
                      WHERE tij.attempts < tij.max_attempts
                        AND tij.cancellation_requested_at IS NULL
                        AND tij.run_after <= now()
                        AND sd.publication_status NOT IN ('deleted', 'published')
                        AND (
                          tij.status = 'uploaded'
                          OR (
                            tij.status IN ('extracting', 'ocr', 'structuring', 'chunking', 'embedding', 'indexing')
                            AND tij.lease_expires_at < now()
                          )
                        )
                      ORDER BY tij.run_after, tij.created_at
                      FOR UPDATE SKIP LOCKED
                      LIMIT 1
                    )
                    UPDATE textbook_ingestion_jobs tij
                    SET status = CASE WHEN tij.status = 'uploaded' THEN 'extracting' ELSE tij.status END,
                        progress = CASE WHEN tij.status = 'uploaded' THEN GREATEST(tij.progress, 1) ELSE tij.progress END,
                        attempts = tij.attempts + 1,
                        worker_id = :worker_id,
                        lease_token = gen_random_uuid(),
                        lease_expires_at = now() + make_interval(secs => :lease_seconds),
                        heartbeat_at = now(),
                        started_at = COALESCE(tij.started_at, now()),
                        error_code = NULL,
                        error_message = NULL,
                        updated_at = now()
                    FROM candidate
                    WHERE tij.id = candidate.id
                    RETURNING tij.*
                    """
                ),
                {"worker_id": worker, "lease_seconds": effective_lease_seconds},
            )
            .mappings()
            .first()
        )
        if not row:
            return None
        event_type = "claimed" if int(row["attempts"]) == 1 else "reclaimed"
        session.execute(
            text(
                """
                INSERT INTO textbook_ingestion_job_events (
                  job_id, status, progress, event_type, message, details
                )
                VALUES (
                  CAST(:job_id AS uuid), :status, :progress, :event_type,
                  'Worker claimed textbook ingestion job', CAST(:details AS jsonb)
                )
                """
            ),
            {
                "job_id": str(row["id"]),
                "status": str(row["status"]),
                "progress": int(row["progress"]),
                "event_type": event_type,
                "details": _json({"worker_id": worker, "attempt": int(row["attempts"])}),
            },
        )
        session.execute(
            text(
                """
                UPDATE source_documents
                SET processing_status = :status,
                    publication_status = 'processing',
                    updated_at = now()
                WHERE id = :document_id
                  AND publication_status IN ('draft', 'processing', 'review_ready', 'failed')
                """
            ),
            {"document_id": str(row["document_id"]), "status": str(row["status"])},
        )
    return _claimed_job(row)


def heartbeat(job: ClaimedIngestionJob, *, lease_seconds: int | None = None) -> None:
    effective_lease_seconds = lease_seconds or get_settings().textbook_ingestion_lease_seconds
    with db_session() as session:
        updated = session.execute(
            text(
                """
                UPDATE textbook_ingestion_jobs
                SET heartbeat_at = now(),
                    lease_expires_at = now() + make_interval(secs => :lease_seconds),
                    updated_at = now()
                WHERE id = CAST(:job_id AS uuid)
                  AND worker_id = :worker_id
                  AND lease_token = CAST(:lease_token AS uuid)
                  AND status IN ('extracting', 'ocr', 'structuring', 'chunking', 'embedding', 'indexing')
                  AND lease_expires_at > now()
                  AND cancellation_requested_at IS NULL
                """
            ),
            {
                "job_id": job.id,
                "worker_id": job.worker_id,
                "lease_token": job.lease_token,
                "lease_seconds": effective_lease_seconds,
            },
        )
    if int(updated.rowcount or 0) != 1:
        raise TextbookJobLeaseLostError(f"Lease lost for textbook ingestion job {job.id}")


def update_job_progress(
    job: ClaimedIngestionJob,
    *,
    progress: int,
    counters: dict[str, int] | None = None,
    stage_metrics: dict[str, Any] | None = None,
    quality_report: dict[str, Any] | None = None,
    message: str | None = None,
) -> None:
    if not 0 <= progress <= 100:
        raise ValueError("progress must be between 0 and 100")
    counter_values = counters or {}
    unknown_counters = set(counter_values) - PROGRESS_COUNTERS
    if unknown_counters:
        raise ValueError(f"Unsupported ingestion counters: {sorted(unknown_counters)}")
    if any(int(value) < 0 for value in counter_values.values()):
        raise ValueError("Ingestion counters must be non-negative")
    counter_sql = "".join(f", {name} = :{name}" for name in sorted(counter_values))
    parameters: dict[str, Any] = {
        "job_id": job.id,
        "worker_id": job.worker_id,
        "lease_token": job.lease_token,
        "status": job.status.value,
        "progress": progress,
        "stage_metrics": _json(stage_metrics or {}),
        "quality_report": _json(quality_report or {}),
        "lease_seconds": get_settings().textbook_ingestion_lease_seconds,
        **{name: int(value) for name, value in counter_values.items()},
    }
    with db_session() as session:
        row = (
            session.execute(
                text(
                    f"""
                    UPDATE textbook_ingestion_jobs
                    SET progress = GREATEST(progress, :progress),
                        stage_metrics = stage_metrics || CAST(:stage_metrics AS jsonb),
                        quality_report = quality_report || CAST(:quality_report AS jsonb),
                        heartbeat_at = now(),
                        lease_expires_at = now() + make_interval(secs => :lease_seconds),
                        updated_at = now()
                        {counter_sql}
                    WHERE id = CAST(:job_id AS uuid)
                      AND worker_id = :worker_id
                      AND lease_token = CAST(:lease_token AS uuid)
                      AND status = :status
                      AND lease_expires_at > now()
                      AND cancellation_requested_at IS NULL
                    RETURNING progress
                    """
                ),
                parameters,
            )
            .mappings()
            .first()
        )
        if not row:
            raise TextbookJobLeaseLostError(f"Lease lost or cancellation requested for textbook ingestion job {job.id}")
        if message:
            session.execute(
                text(
                    """
                    INSERT INTO textbook_ingestion_job_events (
                      job_id, status, progress, event_type, message, details
                    ) VALUES (
                      CAST(:job_id AS uuid), :status, :progress, 'progress', :message,
                      CAST(:details AS jsonb)
                    )
                    """
                ),
                {
                    "job_id": job.id,
                    "status": job.status.value,
                    "progress": int(row["progress"]),
                    "message": message,
                    "details": _json({"counters": counter_values}),
                },
            )


def advance_job(
    job: ClaimedIngestionJob,
    target: IngestionStage | str,
    *,
    progress: int,
    counters: dict[str, int] | None = None,
    stage_metrics: dict[str, Any] | None = None,
    quality_report: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    message: str | None = None,
) -> ClaimedIngestionJob:
    target_stage = IngestionStage(target)
    validate_stage_transition(job.status, target_stage)
    if not 0 <= progress <= 100:
        raise ValueError("progress must be between 0 and 100")
    counter_values = counters or {}
    unknown_counters = set(counter_values) - PROGRESS_COUNTERS
    if unknown_counters:
        raise ValueError(f"Unsupported ingestion counters: {sorted(unknown_counters)}")
    if any(int(value) < 0 for value in counter_values.values()):
        raise ValueError("Ingestion counters must be non-negative")
    output_values = outputs or {}
    projection_run_id = str(output_values.get("projection_run_id") or "").strip()
    if target_stage == IngestionStage.REVIEW_READY:
        if not projection_run_id or projection_run_id != job.lease_token:
            raise ValueError(
                "review_ready requires the verified projection_run_id owned by the current lease"
            )
    counter_sql = "".join(f", {name} = :{name}" for name in sorted(counter_values))
    releases_lease = target_stage not in ACTIVE_INGESTION_STAGES
    if releases_lease:
        finished_sql = ", finished_at = now()" if target_stage == IngestionStage.REVIEW_READY else ""
        lease_sql = f", worker_id = NULL, lease_token = NULL, lease_expires_at = NULL{finished_sql}"
    else:
        lease_sql = ", heartbeat_at = now(), lease_expires_at = now() + make_interval(secs => :lease_seconds)"
    parameters: dict[str, Any] = {
        "job_id": job.id,
        "worker_id": job.worker_id,
        "lease_token": job.lease_token,
        "current_status": job.status.value,
        "target_status": target_stage.value,
        "progress": progress,
        "stage_metrics": _json(stage_metrics or {}),
        "quality_report": _json(quality_report or {}),
        "outputs": _json(output_values),
        "projection_run_id": projection_run_id or None,
        "lease_seconds": get_settings().textbook_ingestion_lease_seconds,
        **{name: int(value) for name, value in counter_values.items()},
    }
    with db_session() as session:
        row = (
            session.execute(
                text(
                    f"""
                    UPDATE textbook_ingestion_jobs
                    SET status = :target_status,
                        progress = :progress,
                        stage_metrics = stage_metrics || CAST(:stage_metrics AS jsonb),
                        quality_report = quality_report || CAST(:quality_report AS jsonb),
                        outputs = outputs || CAST(:outputs AS jsonb),
                        updated_at = now()
                        {counter_sql}
                        {lease_sql}
                    WHERE id = CAST(:job_id AS uuid)
                      AND worker_id = :worker_id
                      AND lease_token = CAST(:lease_token AS uuid)
                      AND status = :current_status
                      AND lease_expires_at > now()
                      AND cancellation_requested_at IS NULL
                    RETURNING *
                    """
                ),
                parameters,
            )
            .mappings()
            .first()
        )
        if not row:
            raise TextbookJobLeaseLostError(f"Lease lost or cancellation requested for textbook ingestion job {job.id}")
        session.execute(
            text(
                """
                INSERT INTO textbook_ingestion_job_events (
                  job_id, status, progress, event_type, message, details
                )
                VALUES (
                  CAST(:job_id AS uuid), :status, :progress, 'stage_changed', :message,
                  CAST(:details AS jsonb)
                )
                """
            ),
            {
                "job_id": job.id,
                "status": target_stage.value,
                "progress": progress,
                "message": message,
                "details": _json({"counters": counter_values, "worker_id": job.worker_id}),
            },
        )
        publication_status = "review_ready" if target_stage == IngestionStage.REVIEW_READY else "processing"
        session.execute(
            text(
                """
                UPDATE source_documents
                SET processing_status = :processing_status,
                    publication_status = :publication_status,
                    active_projection_run_id = CASE
                      WHEN :processing_status = 'review_ready' THEN :projection_run_id
                      ELSE active_projection_run_id
                    END,
                    quality_summary = quality_summary || CAST(:quality_report AS jsonb),
                    updated_at = now()
                WHERE id = :document_id
                """
            ),
            {
                "document_id": job.document_id,
                "processing_status": target_stage.value,
                "publication_status": publication_status,
                "quality_report": _json(quality_report or {}),
                "projection_run_id": projection_run_id or None,
            },
        )
    if releases_lease:
        return replace(job, status=target_stage, worker_id="", lease_token="")
    return replace(job, status=target_stage)


def fail_job(job: ClaimedIngestionJob, *, error_code: str, error_message: str) -> None:
    message = " ".join(error_message.split())[:1000]
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE textbook_ingestion_jobs
                    SET status = 'failed',
                        error_code = :error_code,
                        error_message = :error_message,
                        worker_id = NULL,
                        lease_token = NULL,
                        lease_expires_at = NULL,
                        finished_at = now(),
                        updated_at = now()
                    WHERE id = CAST(:job_id AS uuid)
                      AND worker_id = :worker_id
                      AND lease_token = CAST(:lease_token AS uuid)
                      AND status = :status
                      AND lease_expires_at > now()
                      AND cancellation_requested_at IS NULL
                    RETURNING document_id, progress
                    """
                ),
                {
                    "job_id": job.id,
                    "worker_id": job.worker_id,
                    "lease_token": job.lease_token,
                    "status": job.status.value,
                    "error_code": error_code[:120],
                    "error_message": message,
                },
            )
            .mappings()
            .first()
        )
        if not row:
            raise TextbookJobLeaseLostError(f"Lease lost for textbook ingestion job {job.id}")
        session.execute(
            text(
                """
                INSERT INTO textbook_ingestion_job_events (
                  job_id, status, progress, event_type, message, details
                ) VALUES (
                  CAST(:job_id AS uuid), 'failed', :progress, 'failed',
                  :message, CAST(:details AS jsonb)
                )
                """
            ),
            {
                "job_id": job.id,
                "progress": int(row["progress"]),
                "message": message,
                "details": _json({"error_code": error_code[:120]}),
            },
        )
        session.execute(
            text(
                """
                UPDATE source_documents
                SET processing_status = 'failed',
                    publication_status = 'failed',
                    active_projection_run_id = NULL,
                    quality_summary = quality_summary || COALESCE(
                      (SELECT quality_report FROM textbook_ingestion_jobs WHERE id = CAST(:job_id AS uuid)),
                      '{}'::jsonb
                    ),
                    updated_at = now()
                WHERE id = :document_id
                """
            ),
            {"document_id": job.document_id, "job_id": job.id},
        )


def release_job_for_retry(
    job: ClaimedIngestionJob,
    *,
    error_code: str,
    error_message: str,
    base_delay_seconds: int = 30,
) -> bool:
    if job.attempts >= job.max_attempts:
        return False
    message = " ".join(error_message.split())[:1000]
    delay_seconds = min(max(1, base_delay_seconds) * (2 ** max(0, job.attempts - 1)), 900)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE textbook_ingestion_jobs
                    SET status = 'uploaded',
                        resume_from_status = :resume_from_status,
                        error_code = :error_code,
                        error_message = :error_message,
                        worker_id = NULL,
                        lease_token = NULL,
                        lease_expires_at = NULL,
                        run_after = now() + make_interval(secs => :delay_seconds),
                        updated_at = now()
                    WHERE id = CAST(:job_id AS uuid)
                      AND worker_id = :worker_id
                      AND lease_token = CAST(:lease_token AS uuid)
                      AND status = :status
                      AND lease_expires_at > now()
                      AND cancellation_requested_at IS NULL
                    RETURNING document_id, progress
                    """
                ),
                {
                    "job_id": job.id,
                    "worker_id": job.worker_id,
                    "lease_token": job.lease_token,
                    "status": job.status.value,
                    "resume_from_status": job.status.value,
                    "error_code": error_code[:120],
                    "error_message": message,
                    "delay_seconds": delay_seconds,
                },
            )
            .mappings()
            .first()
        )
        if not row:
            raise TextbookJobLeaseLostError(f"Lease lost or cancellation requested for textbook ingestion job {job.id}")
        session.execute(
            text(
                """
                INSERT INTO textbook_ingestion_job_events (
                  job_id, status, progress, event_type, message, details
                ) VALUES (
                  CAST(:job_id AS uuid), 'uploaded', :progress, 'retry_scheduled',
                  :message, CAST(:details AS jsonb)
                )
                """
            ),
            {
                "job_id": job.id,
                "progress": int(row["progress"]),
                "message": message,
                "details": _json(
                    {
                        "error_code": error_code[:120],
                        "resume_from_status": job.status.value,
                        "delay_seconds": delay_seconds,
                        "attempt": job.attempts,
                    }
                ),
            },
        )
        session.execute(
            text(
                """
                UPDATE source_documents
                SET processing_status = 'uploaded',
                    publication_status = 'draft',
                    active_projection_run_id = NULL,
                    updated_at = now()
                WHERE id = :document_id
                  AND publication_status NOT IN ('published', 'deleted')
                """
            ),
            {"document_id": job.document_id},
        )
    return True


def cancellation_requested(job: ClaimedIngestionJob) -> bool:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT cancellation_requested_at
                    FROM textbook_ingestion_jobs
                    WHERE id = CAST(:job_id AS uuid)
                      AND worker_id = :worker_id
                      AND lease_token = CAST(:lease_token AS uuid)
                      AND status = :status
                    """
                ),
                {
                    "job_id": job.id,
                    "worker_id": job.worker_id,
                    "lease_token": job.lease_token,
                    "status": job.status.value,
                },
            )
            .mappings()
            .first()
        )
    if not row:
        raise TextbookJobLeaseLostError(f"Lease lost for textbook ingestion job {job.id}")
    return row["cancellation_requested_at"] is not None


def acknowledge_cancellation(job: ClaimedIngestionJob) -> None:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE textbook_ingestion_jobs
                    SET status = 'cancelled',
                        worker_id = NULL,
                        lease_token = NULL,
                        lease_expires_at = NULL,
                        finished_at = now(),
                        updated_at = now()
                    WHERE id = CAST(:job_id AS uuid)
                      AND worker_id = :worker_id
                      AND lease_token = CAST(:lease_token AS uuid)
                      AND status = :status
                      AND cancellation_requested_at IS NOT NULL
                    RETURNING document_id, progress
                    """
                ),
                {
                    "job_id": job.id,
                    "worker_id": job.worker_id,
                    "lease_token": job.lease_token,
                    "status": job.status.value,
                },
            )
            .mappings()
            .first()
        )
        if not row:
            raise TextbookJobLeaseLostError(f"Cancellation cannot be acknowledged for textbook ingestion job {job.id}")
        session.execute(
            text(
                """
                INSERT INTO textbook_ingestion_job_events (
                  job_id, status, progress, event_type, message, details
                ) VALUES (
                  CAST(:job_id AS uuid), 'cancelled', :progress, 'cancelled',
                  'Textbook ingestion cancelled by request', '{}'::jsonb
                )
                """
            ),
            {"job_id": job.id, "progress": int(row["progress"])},
        )
        session.execute(
            text(
                """
                UPDATE source_documents
                SET processing_status = 'cancelled',
                    publication_status = 'draft',
                    active_projection_run_id = NULL,
                    updated_at = now()
                WHERE id = :document_id
                  AND publication_status NOT IN ('published', 'deleted')
                """
            ),
            {"document_id": job.document_id},
        )


def request_cancellation(job_id: str, *, actor_id: str | None) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT id, document_id, status, progress,
                           worker_id IS NOT NULL
                             AND lease_token IS NOT NULL
                             AND lease_expires_at > now() AS lease_active
                    FROM textbook_ingestion_jobs
                    WHERE id = CAST(:job_id AS uuid)
                    FOR UPDATE
                    """
                ),
                {"job_id": job_id},
            )
            .mappings()
            .first()
        )
        if not row:
            raise TextbookIngestionError("ingestion_job_not_found", "Textbook ingestion job not found", status_code=404)
        current = IngestionStage(str(row["status"]))
        if current in {
            IngestionStage.READY,
            IngestionStage.REVIEW_READY,
            IngestionStage.CANCELLED,
        }:
            raise TextbookIngestionError(
                "job_not_cancellable",
                f"A {current.value} ingestion job cannot be cancelled",
                status_code=409,
            )
        immediate = current not in ACTIVE_INGESTION_STAGES or not bool(row.get("lease_active"))
        next_status = IngestionStage.CANCELLED.value if immediate else current.value
        session.execute(
            text(
                """
                UPDATE textbook_ingestion_jobs
                SET status = :status,
                    cancellation_requested_at = now(),
                    worker_id = CASE WHEN :immediate THEN NULL ELSE worker_id END,
                    lease_token = CASE WHEN :immediate THEN NULL ELSE lease_token END,
                    lease_expires_at = CASE WHEN :immediate THEN NULL ELSE lease_expires_at END,
                    finished_at = CASE WHEN :immediate THEN now() ELSE finished_at END,
                    updated_at = now()
                WHERE id = CAST(:job_id AS uuid)
                """
            ),
            {"job_id": job_id, "status": next_status, "immediate": immediate},
        )
        session.execute(
            text(
                """
                INSERT INTO textbook_ingestion_job_events (
                  job_id, status, progress, event_type, message, details
                ) VALUES (
                  CAST(:job_id AS uuid), :status, :progress, 'cancel_requested',
                  'Textbook ingestion cancellation requested', '{}'::jsonb
                )
                """
            ),
            {"job_id": job_id, "status": next_status, "progress": int(row["progress"])},
        )
        if immediate:
            session.execute(
                text(
                    """
                    UPDATE source_documents
                    SET processing_status = 'cancelled',
                        publication_status = 'draft',
                        active_projection_run_id = NULL,
                        updated_at = now()
                    WHERE id = :document_id
                      AND publication_status NOT IN ('published', 'deleted')
                    """
                ),
                {"document_id": str(row["document_id"])},
            )
        session.execute(
            text(
                """
                INSERT INTO textbook_lifecycle_events (document_id, job_id, action, actor_id, details)
                VALUES (:document_id, CAST(:job_id AS uuid), 'cancel', CAST(:actor_id AS uuid), '{}'::jsonb)
                """
            ),
            {"document_id": str(row["document_id"]), "job_id": job_id, "actor_id": actor_id},
        )
    from server.app.domains.textbook_ingestion.repository import get_ingestion_job

    return get_ingestion_job(job_id)


def retry_job(job_id: str, *, actor_id: str | None) -> dict[str, Any]:
    settings = effective_ingestion_settings()
    snapshot = processing_config_snapshot(settings)
    fingerprint = processing_fingerprint(snapshot)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT id, document_id, status, progress, attempts, max_attempts
                    FROM textbook_ingestion_jobs
                    WHERE id = CAST(:job_id AS uuid)
                    FOR UPDATE
                    """
                ),
                {"job_id": job_id},
            )
            .mappings()
            .first()
        )
        if not row:
            raise TextbookIngestionError("ingestion_job_not_found", "Textbook ingestion job not found", status_code=404)
        current = IngestionStage(str(row["status"]))
        if current not in {
            IngestionStage.FAILED,
            IngestionStage.CANCELLED,
            IngestionStage.AWAITING_OCR,
            IngestionStage.REVIEW_READY,
        }:
            raise TextbookIngestionError(
                "job_not_retryable",
                f"A {current.value} ingestion job cannot be retried",
                status_code=409,
            )
        session.execute(
            text(
                """
                UPDATE textbook_ingestion_jobs
                SET status = 'uploaded',
                    progress = 0,
                    resume_from_status = :resume_from_status,
                    max_attempts = GREATEST(max_attempts, attempts + 3),
                    worker_id = NULL,
                    lease_token = NULL,
                    lease_expires_at = NULL,
                    heartbeat_at = NULL,
                    run_after = now(),
                    processing_fingerprint = :processing_fingerprint,
                    idempotency_key = document_id || ':' || :processing_fingerprint,
                    config_snapshot = CAST(:config_snapshot AS jsonb),
                    error_code = NULL,
                    error_message = NULL,
                    cancellation_requested_at = NULL,
                    finished_at = NULL,
                    updated_at = now()
                WHERE id = CAST(:job_id AS uuid)
                """
            ),
            {
                "job_id": job_id,
                "resume_from_status": current.value,
                "processing_fingerprint": fingerprint,
                "config_snapshot": _json(snapshot),
            },
        )
        session.execute(
            text(
                """
                UPDATE source_documents
                SET processing_status = 'uploaded',
                    publication_status = 'draft',
                    processing_fingerprint = :processing_fingerprint,
                    active_projection_run_id = NULL,
                    updated_at = now()
                WHERE id = :document_id
                """
            ),
            {"document_id": str(row["document_id"]), "processing_fingerprint": fingerprint},
        )
        session.execute(
            text(
                """
                INSERT INTO textbook_ingestion_job_events (
                  job_id, status, progress, event_type, message, details
                ) VALUES (
                  CAST(:job_id AS uuid), 'uploaded', 0, 'retry',
                  'Textbook ingestion queued for retry', CAST(:details AS jsonb)
                )
                """
            ),
            {"job_id": job_id, "details": _json({"resume_from_status": current.value})},
        )
        session.execute(
            text(
                """
                INSERT INTO textbook_lifecycle_events (document_id, job_id, action, actor_id, details)
                VALUES (
                  :document_id, CAST(:job_id AS uuid), 'retry', CAST(:actor_id AS uuid),
                  CAST(:details AS jsonb)
                )
                """
            ),
            {
                "document_id": str(row["document_id"]),
                "job_id": job_id,
                "actor_id": actor_id,
                "details": _json({"resume_from_status": current.value}),
            },
        )
    from server.app.domains.textbook_ingestion.repository import get_ingestion_job

    return get_ingestion_job(job_id)
